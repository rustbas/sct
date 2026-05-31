from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sct import __version__
from sct.core.doctor import DoctorReport
from sct.core.errors import EXIT_OK, EXIT_NOT_FOUND, EXIT_STALE, EXIT_USAGE, SctError
from sct.core.models import Status
from sct.core.service import TodoService


def _print_items(items, *, as_json: bool) -> None:
    if as_json:
        payload = {
            "version": __version__,
            "items": [i.to_dict() for i in items],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for item in items:
        mark = " " if item.status == Status.OPEN else "x"
        print(f"[{mark}] P{item.priority}  {item.file}:{item.line}: {item.task}")


def _print_doctor(report: DoctorReport) -> None:
    if report.ok:
        print("OK — no issues found.")
        return
    if report.stale_files:
        print("Stale or missing files (run `sct sync`):")
        for line in report.stale_files:
            print(f"  - {line}")
    if report.orphan_items:
        print("Cache entries out of date:")
        for line in report.orphan_items:
            print(f"  - {line}")
    if report.duplicate_tasks:
        print("Duplicate task text in same file:")
        for file, task, count in report.duplicate_tasks:
            print(f"  - {file}: {task!r} ({count}x)")
    if report.missing_in_cache or report.extra_in_cache:
        print(
            f"Cache drift: {report.missing_in_cache} missing, "
            f"{report.extra_in_cache} extra (run `sct sync --full`)"
        )


def _handle_error(err: BaseException) -> None:
    if isinstance(err, SctError):
        print(err, file=sys.stderr)
        sys.exit(err.exit_code)
    print(err, file=sys.stderr)
    sys.exit(EXIT_NOT_FOUND)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="sct",
        description="Source Code Todo — scan and manage TODO/DONE markers in source files",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root (default: search upward for .sct/)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    sub = parser.add_subparsers(dest="command")

    p_sync = sub.add_parser("sync", help="Scan sources and update JSON cache")
    p_sync.add_argument(
        "--full",
        action="store_true",
        help="Rescan all files (default: incremental)",
    )
    p_sync.add_argument("-v", "--verbose", action="store_true")

    p_list = sub.add_parser("list", help="List todos from cache")
    p_list.add_argument("--all", action="store_true", help="Include done items")
    p_list.add_argument("--priority", type=int, choices=(1, 2, 3))
    p_list.add_argument("--json", action="store_true", dest="as_json")

    p_done = sub.add_parser("done", help="Mark todo as DONE in source (keeps priority)")
    p_done.add_argument("ref", help="Item id or file:line")
    p_done.add_argument("--dry-run", action="store_true")

    p_reopen = sub.add_parser("reopen", help="Mark done item as TODO in source")
    p_reopen.add_argument("ref", help="Item id or file:line")

    p_show = sub.add_parser("show", help="Show one item")
    p_show.add_argument("ref")
    p_show.add_argument("--json", action="store_true", dest="as_json")

    p_doctor = sub.add_parser("doctor", help="Check cache vs source files")
    p_doctor.add_argument(
        "--compare",
        action="store_true",
        help="Compare full rescan with cache",
    )

    sub.add_parser("init", help="Create .sct/config.json from example")

    sub.add_parser("tui", help="Open interactive TUI")

    args = parser.parse_args(argv)

    if args.command is None:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            print("sct: TUI requires a terminal; use subcommands.", file=sys.stderr)
            sys.exit(EXIT_USAGE)
        try:
            svc = TodoService(args.root)
            _run_tui(svc)
        except SctError as e:
            _handle_error(e)
        return

    try:
        svc = TodoService(args.root)
    except SctError as e:
        _handle_error(e)
        return

    try:
        if args.command == "sync":
            cache = svc.sync(full=args.full, verbose=args.verbose)
            print(f"Synced {len(cache.items)} item(s) -> {svc.config.cache_path}")
            return

        if args.command == "init":
            path = svc.init_project()
            print(f"Config: {path}")
            return

        if args.command == "doctor":
            report = svc.doctor(resync_compare=args.compare)
            _print_doctor(report)
            sys.exit(EXIT_OK if report.ok else EXIT_STALE)
            return

        if args.command == "list":
            if not svc.config.cache_path.is_file():
                svc.sync()
            status = None if args.all else Status.OPEN
            items = svc.list_items(status=status, priority=args.priority)
            _print_items(items, as_json=args.as_json)
            return

        if args.command == "done":
            if args.dry_run:
                old, new = svc.preview_done(args.ref)
                print(old)
                print("->")
                print(new)
                return
            item = svc.done(args.ref)
            print(item.list_line())
            return

        if args.command == "reopen":
            item = svc.reopen(args.ref)
            print(item.list_line())
            return

        if args.command == "show":
            item = svc.resolve(args.ref)
            if item is None:
                raise SctError(f"Not found: {args.ref}", EXIT_NOT_FOUND)
            if args.as_json:
                print(json.dumps(item.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(f"id:       {item.id}")
                print(f"file:     {item.file}:{item.line}")
                print(f"status:   {item.status.value}")
                print(f"priority: {item.priority}")
                print(f"marker:   {item.marker}")
                print(f"task:     {item.task}")
            return

        if args.command == "tui":
            if not sys.stdin.isatty() or not sys.stdout.isatty():
                print("sct: TUI requires a terminal.", file=sys.stderr)
                sys.exit(EXIT_USAGE)
            _run_tui(svc)
            return

        parser.print_help()
    except SctError as e:
        _handle_error(e)


def _run_tui(svc: TodoService) -> None:
    from sct.tui.app import run_tui

    run_tui(svc)


if __name__ == "__main__":
    main()

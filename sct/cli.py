from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sct.core.models import Status
from sct.core.service import TodoService


def _print_items(items, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps([i.to_dict() for i in items], ensure_ascii=False, indent=2))
        return
    for item in items:
        mark = " " if item.status == Status.OPEN else "x"
        print(f"[{mark}] P{item.priority}  {item.file}:{item.line}: {item.task}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="sct",
        description="Source Code Todo — scan and manage TODO/DONE markers in source files",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root (default: current directory)",
    )
    sub = parser.add_subparsers(dest="command")

    p_sync = sub.add_parser("sync", help="Scan sources and update JSON cache")
    p_sync.add_argument("--full", action="store_true", default=True)

    p_list = sub.add_parser("list", help="List todos from cache")
    p_list.add_argument("--all", action="store_true", help="Include done items")
    p_list.add_argument("--json", action="store_true", dest="as_json")

    p_done = sub.add_parser("done", help="Mark todo as DONE in source (keeps priority)")
    p_done.add_argument("ref", help="Item id or file:line")
    p_done.add_argument("--dry-run", action="store_true")

    p_reopen = sub.add_parser("reopen", help="Mark done item as TODO in source")
    p_reopen.add_argument("ref", help="Item id or file:line")

    p_show = sub.add_parser("show", help="Show one item")
    p_show.add_argument("ref")
    p_show.add_argument("--json", action="store_true", dest="as_json")

    sub.add_parser("tui", help="Open interactive TUI")

    args = parser.parse_args(argv)
    svc = TodoService(args.root)

    if args.command is None:
        _run_tui(svc)
        return

    if args.command == "sync":
        cache = svc.sync()
        print(f"Synced {len(cache.items)} item(s) -> {svc.config.cache_path}")
        return

    if args.command == "list":
        status = None if args.all else Status.OPEN
        if not svc.config.cache_path.is_file():
            svc.sync()
        items = svc.list_items(status=status)
        _print_items(items, as_json=args.as_json)
        return

    if args.command == "done":
        if args.dry_run:
            old, new = svc.preview_done(args.ref)
            print(old)
            print("->")
            print(new)
            return
        try:
            item = svc.done(args.ref)
        except KeyError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        print(item.list_line())
        return

    if args.command == "reopen":
        try:
            item = svc.reopen(args.ref)
        except KeyError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        print(item.list_line())
        return

    if args.command == "show":
        item = svc.resolve(args.ref)
        if item is None:
            print(f"Not found: {args.ref}", file=sys.stderr)
            sys.exit(1)
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
        _run_tui(svc)
        return

    parser.print_help()


def _run_tui(svc: TodoService) -> None:
    from sct.tui.app import run_tui

    run_tui(svc)


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Input, Static

from sct.core.errors import SctError
from sct.core.models import Status, TodoItem
from sct.core.service import TodoService

THEME_CSS = Path(__file__).with_name("theme.tcss")


class ConfirmDoneScreen(ModalScreen[bool]):
    """Yes/No modal before patching source."""

    CSS_PATH = THEME_CSS

    BINDINGS = [
        Binding("y", "confirm", "Yes", show=False),
        Binding("n", "cancel", "No", show=False),
        Binding("escape", "cancel", "No", show=False),
        Binding("q", "cancel", "No", show=False),
    ]

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)

    def __init__(self, item: TodoItem, old_line: str, new_line: str) -> None:
        super().__init__()
        self.item = item
        self.old_line = old_line
        self.new_line = new_line

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static(f"done  {self.item.file}:{self.item.line}", id="confirm-title"),
            Static(""),
            Static(self.old_line, id="confirm-old"),
            Static("↓", id="confirm-arrow"),
            Static(self.new_line, id="confirm-new"),
            Static(""),
            Static("y yes   n no   esc cancel", id="confirm-hint"),
            id="confirm-body",
        )


class FilterScreen(ModalScreen[str | None]):
    """Filter prompt (/)."""

    CSS_PATH = THEME_CSS

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, current: str) -> None:
        super().__init__()
        self.current = current

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("filter", id="filter-title"),
            Input(value=self.current, placeholder="substring…", id="filter-input"),
            Static("enter apply   esc cancel", id="filter-hint"),
            id="filter-body",
        )

    def on_mount(self) -> None:
        self.query_one("#filter-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())

    def action_cancel(self) -> None:
        self.dismiss(None)


class SctApp(App):
    """TUI with vim-like keys and a minimal dark theme."""

    TITLE = "sct"
    CSS_PATH = THEME_CSS

    BINDINGS = [
        # vim navigation
        Binding("j,down", "move_down", "Down", show=False),
        Binding("k,up", "move_up", "Up", show=False),
        Binding("g", "move_top", "Top", show=False),
        Binding("G", "move_bottom", "Bottom", show=False),
        Binding("ctrl+d", "page_down", "PgDown", show=False),
        Binding("ctrl+u", "page_up", "PgUp", show=False),
        # actions (lf-style single letters)
        Binding("q", "quit", "Quit", show=False),
        Binding("r", "refresh", "Sync", show=False),
        Binding("d", "done", "Done", show=False),
        Binding("o", "reopen", "Reopen", show=False),
        Binding("a", "toggle_all", "All", show=False),
        Binding("/", "focus_search", "Filter", show=False),
        Binding("?", "help", "Help", show=False),
    ]

    def __init__(self, service: TodoService) -> None:
        super().__init__()
        self.service = service
        self.show_done = False
        self.filter_text = ""
        self._rows: list[TodoItem] = []
        self._selected_id: str | None = None

    def compose(self) -> ComposeResult:
        root = str(self.service.config.root)
        yield Static(f" sct  {root}", id="title-bar")
        yield DataTable(id="tasks", zebra_stripes=False, show_header=True)
        yield Static("", id="detail")
        yield Static("", id="status-bar")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("p", "s", "file", "line", "task")
        table.cursor_type = "row"
        table.focus()
        report = self.service.doctor()
        if not report.ok:
            self.notify("stale cache — r sync", severity="warning", timeout=5)
        self._sync_background()
        self._update_status_line()

    def _table(self) -> DataTable:
        return self.query_one("#tasks", DataTable)

    def action_move_down(self) -> None:
        self._table().action_cursor_down()

    def action_move_up(self) -> None:
        self._table().action_cursor_up()

    def action_move_top(self) -> None:
        table = self._table()
        if table.row_count:
            table.move_cursor(row=0)

    def action_move_bottom(self) -> None:
        table = self._table()
        if table.row_count:
            table.move_cursor(row=table.row_count - 1)

    def action_page_down(self) -> None:
        table = self._table()
        for _ in range(10):
            table.action_cursor_down()

    def action_page_up(self) -> None:
        table = self._table()
        for _ in range(10):
            table.action_cursor_up()

    @work(thread=True)
    def _sync_background(self) -> None:
        self.service.sync()
        self.call_from_thread(self._reload_table)

    def _reload_table(self) -> None:
        status = None if self.show_done else Status.OPEN
        items = self.service.list_items(status=status, use_cache=True)
        ft = self.filter_text.lower()
        if ft:
            items = [
                i
                for i in items
                if ft in i.task.lower() or ft in i.file.lower()
            ]
        self._rows = items
        table = self._table()
        table.clear()
        for item in items:
            st = "×" if item.status == Status.DONE else " "
            table.add_row(
                str(item.priority),
                st,
                item.file,
                str(item.line),
                item.task,
                key=item.id,
            )
        if table.row_count:
            table.focus()
        self._update_status_line()
        self._update_detail()

    def _update_status_line(self) -> None:
        open_n = sum(1 for i in self.service.list_items(status=Status.OPEN))
        done_n = sum(1 for i in self.service.list_items(status=Status.DONE))
        mode = "all" if self.show_done else "open"
        filt = f'  /{self.filter_text}' if self.filter_text else ""
        shown = len(self._rows)
        self.query_one("#status-bar", Static).update(
            f" {shown} {mode}  open:{open_n}  done:{done_n}{filt}"
            f" │ jk move  d done  o reopen  r sync  a all  / filter  ? help  q quit"
        )

    def _selected_item(self) -> TodoItem | None:
        if not self._selected_id:
            return None
        return self.service.get(self._selected_id)

    def _update_detail(self) -> None:
        item = self._selected_item()
        detail = self.query_one("#detail", Static)
        if item is None:
            detail.update("")
            return
        detail.update(f" {item.marker}  {item.file}:{item.line}  {item.task}")

    @on(DataTable.RowHighlighted)
    def _on_row_highlight(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is not None:
            self._selected_id = str(event.row_key.value)
        self._update_detail()

    def action_refresh(self) -> None:
        self.notify("sync", severity="information", timeout=1)
        self._sync_background()

    def action_toggle_all(self) -> None:
        self.show_done = not self.show_done
        self._reload_table()

    def action_focus_search(self) -> None:
        self.push_screen(
            FilterScreen(self.filter_text),
            self._on_filter_result,
        )

    def _on_filter_result(self, text: str | None) -> None:
        if text is not None:
            self.filter_text = text
            self._reload_table()

    def action_help(self) -> None:
        self.notify(
            "j/k g/G move  d done  o reopen  r sync  a all/open  / filter  q quit",
            timeout=8,
        )

    def action_done(self) -> None:
        item = self._selected_item()
        if item is None:
            self.notify("no selection", severity="warning")
            return
        if item.status == Status.DONE:
            self.notify("already done", severity="warning")
            return
        try:
            old, new = self.service.preview_done(item.id)
        except (SctError, OSError, ValueError) as e:
            self.notify(str(e), severity="error")
            return

        def on_confirm(ok: bool | None) -> None:
            if not ok:
                return
            try:
                self.service.done(item.id)
            except (SctError, OSError, ValueError) as e:
                self.notify(str(e), severity="error")
                return
            self.notify(f"done {item.file}:{item.line}", timeout=2)
            self._reload_table()

        self.push_screen(ConfirmDoneScreen(item, old, new), on_confirm)

    def action_reopen(self) -> None:
        item = self._selected_item()
        if item is None:
            self.notify("no selection", severity="warning")
            return
        if item.status == Status.OPEN:
            self.notify("already open", severity="warning")
            return
        try:
            self.service.reopen(item.id)
        except (SctError, OSError, ValueError) as e:
            self.notify(str(e), severity="error")
            return
        self.notify(f"reopen {item.file}:{item.line}", timeout=2)
        self._reload_table()


def run_tui(service: TodoService) -> None:
    app = SctApp(service)
    app.run()

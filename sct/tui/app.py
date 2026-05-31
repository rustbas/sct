from __future__ import annotations

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Footer, Header, Label, Static

from sct.core.models import Status, TodoItem
from sct.core.service import TodoService


class ConfirmDoneScreen(ModalScreen[bool]):
    """Yes/No modal before patching source."""

    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "No"),
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
            Static(f"Mark as DONE?  [bold]{self.item.file}:{self.item.line}[/]"),
            Static(""),
            Static("[dim]Before:[/]"),
            Static(self.old_line),
            Static(""),
            Static("[dim]After:[/]"),
            Static(self.new_line),
            Static(""),
            Static("[bold]y[/] confirm  [bold]n[/] cancel"),
            id="confirm-body",
        )


class SctApp(App):
    TITLE = "sct — Source Code Todo"
    CSS = """
    Screen {
        layout: vertical;
    }
    #status-bar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text-muted;
        padding: 0 1;
    }
    DataTable {
        height: 1fr;
    }
    #detail {
        height: 3;
        padding: 0 1;
        background: $panel;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Sync"),
        Binding("d", "done", "Done"),
        Binding("o", "reopen", "Reopen"),
        Binding("a", "toggle_all", "All/Open"),
        Binding("slash", "focus_search", "Filter", show=False),
        Binding("question_mark", "help", "Help"),
    ]

    def __init__(self, service: TodoService) -> None:
        super().__init__()
        self.service = service
        self.show_done = False
        self.filter_text = ""
        self._rows: list[TodoItem] = []
        self._selected_id: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="tasks", zebra_stripes=True)
        yield Static("", id="detail")
        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("P", "S", "File", "Line", "Task")
        table.cursor_type = "row"
        self._sync_background()

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
        table = self.query_one(DataTable)
        table.clear()
        for item in items:
            st = "x" if item.status == Status.DONE else " "
            table.add_row(
                str(item.priority),
                st,
                item.file,
                str(item.line),
                item.task,
                key=item.id,
            )
        open_n = sum(1 for i in self.service.list_items(status=Status.OPEN))
        done_n = sum(1 for i in self.service.list_items(status=Status.DONE))
        mode = "all" if self.show_done else "open"
        filt = f'  filter="{self.filter_text}"' if self.filter_text else ""
        self.query_one("#status-bar", Static).update(
            f"{len(items)} shown ({mode}) | open={open_n} done={done_n}{filt} | r=sync d=done o=reopen a=toggle q=quit"
        )
        self._update_detail()

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
        detail.update(
            f"[bold]{item.marker}[/]  {item.file}:{item.line}  id={item.id}  |  {item.task}"
        )

    @on(DataTable.RowHighlighted)
    def _on_row_highlight(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key is not None:
            self._selected_id = str(event.row_key.value)
        self._update_detail()

    def action_refresh(self) -> None:
        self.notify("Syncing…")
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
            "r sync | d done | o reopen | a all/open | / filter | Enter detail | q quit"
        )

    def action_done(self) -> None:
        item = self._selected_item()
        if item is None:
            self.notify("No selection", severity="warning")
            return
        if item.status == Status.DONE:
            self.notify("Already done", severity="warning")
            return
        try:
            old, new = self.service.preview_done(item.id)
        except (KeyError, OSError, ValueError) as e:
            self.notify(str(e), severity="error")
            return

        def on_confirm(ok: bool | None) -> None:
            if not ok:
                return
            try:
                self.service.done(item.id)
            except (KeyError, OSError, ValueError) as e:
                self.notify(str(e), severity="error")
                return
            self.notify(f"Done: {item.file}:{item.line}")
            self._reload_table()

        self.push_screen(ConfirmDoneScreen(item, old, new), on_confirm)

    def action_reopen(self) -> None:
        item = self._selected_item()
        if item is None:
            self.notify("No selection", severity="warning")
            return
        if item.status == Status.OPEN:
            self.notify("Already open", severity="warning")
            return
        try:
            self.service.reopen(item.id)
        except (KeyError, OSError, ValueError) as e:
            self.notify(str(e), severity="error")
            return
        self.notify(f"Reopened: {item.file}:{item.line}")
        self._reload_table()


class FilterScreen(ModalScreen[str | None]):
    """Simple filter prompt."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, current: str) -> None:
        super().__init__()
        self.current = current

    def compose(self) -> ComposeResult:
        from textual.widgets import Input

        yield Vertical(
            Static("Filter (file or task substring). Empty = clear."),
            Input(value=self.current, placeholder="filter…", id="filter-input"),
            id="filter-body",
        )

    def on_mount(self) -> None:
        self.query_one("#filter-input").focus()

    def on_input_submitted(self, event) -> None:
        self.dismiss(event.value.strip())

    def action_cancel(self) -> None:
        self.dismiss(None)


def run_tui(service: TodoService) -> None:
    app = SctApp(service)
    app.run()

"""Books tab: the sorting controls and the table of books."""
from PyQt5.QtWidgets import (QAbstractItemView, QHeaderView, QLabel,
                             QTableView, QVBoxLayout, QWidget)

from core.book import Book
from ui.book_table_model import BookTableModel
from ui.sort_panel import SortPanel
from ui.sort_worker import SortThread

# Starting widths (pixels) for every column EXCEPT the title.
# The title column has no fixed width: it stretches to fill the window.
COLUMN_WIDTHS = {
    "author": 160, "genre": 110, "publisher": 170,
    "language": 70, "year": 60, "pages": 60, "editions": 70,
}


class BooksTab(QWidget):
    def __init__(self):
        super().__init__()
        self.model = BookTableModel()
        self._books = []        # the ORIGINAL (unsorted) list; sorts always start from it
        self._sort_thread = None

        self.sort_panel = SortPanel()
        self.sort_panel.sort_requested.connect(self._start_sort)
        self.sort_panel.reset_requested.connect(self._reset_order)

        self.table = self._create_table()

        # Count label: bold, slightly larger, with a little padding
        self.count_label = QLabel()
        self.count_label.setStyleSheet(
            "font-size: 15px; font-weight: bold; padding: 4px 2px;")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(self.sort_panel)
        layout.addWidget(self.count_label)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.show_books([])

    def _create_table(self):
        """Build and configure the table view."""
        table = QTableView()
        table.setModel(self.model)
        table.setAlternatingRowColors(True)                       # striped rows
        table.setSelectionBehavior(QAbstractItemView.SelectRows)  # click selects a row
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)   # read-only
        table.setShowGrid(False)                                  # cleaner look
        table.verticalHeader().setDefaultSectionSize(26)          # compact rows
        # NOTE: we do NOT enable Qt's built-in sorting. Sorting is done
        # by OUR OWN algorithms (see the sorting panel).

        # The title column stretches to take ALL leftover width; the other
        # columns start at a fixed width and can be resized by dragging.
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(60)
        for position, name in enumerate(Book.column_names()):
            if name == "title":
                header.setSectionResizeMode(position, QHeaderView.Stretch)
            else:
                table.setColumnWidth(position, COLUMN_WIDTHS[name])
        return table

    # ---------- showing books ----------
    def show_books(self, books):
        """Show a new list of books (e.g. after loading or scraping)."""
        self._books = books
        self._display(books)

    def _display(self, books):
        """Put a list of books in the table (no change to the original list)."""
        self.model.set_books(books)
        self.count_label.setText(f"Showing {len(books):,} books")

    # ---------- sorting ----------
    def _start_sort(self, algorithm_name, column, descending):
        if not self._books:
            self.sort_panel.show_status("No books loaded yet.")
            return
        self.sort_panel.set_busy(True)
        # The sort runs in a background thread so the window stays responsive
        self._sort_thread = SortThread(algorithm_name, self._books,
                                       column, descending)
        self._sort_thread.sort_finished.connect(self._on_sort_finished)
        self._sort_thread.sort_failed.connect(self._on_sort_failed)
        self._sort_thread.start()

    def _on_sort_finished(self, result):
        self._display(result.sorted_books)
        self.sort_panel.show_result(result)
        self.sort_panel.set_busy(False)

    def _on_sort_failed(self, message):
        self.sort_panel.set_busy(False)
        self.sort_panel.show_status(f"Sort failed: {message}")

    def _reset_order(self):
        """Show the books in their original order again."""
        self._display(self._books)
        self.sort_panel.clear_result()

    def finish_sort(self):
        """Wait for a running sort to end (called when the window closes)."""
        if self._sort_thread is not None and self._sort_thread.isRunning():
            self._sort_thread.wait()
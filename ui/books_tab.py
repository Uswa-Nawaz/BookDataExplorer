"""Books tab: search bar, sorting controls and the table of books."""
from PyQt5.QtWidgets import (QAbstractItemView, QHeaderView, QLabel,
                             QTableView, QVBoxLayout, QWidget)

from algorithms.searching import make_condition, run_search
from core.book import Book
from ui.benchmark_dialog import BenchmarkDialog
from ui.benchmark_worker import BenchmarkThread
from ui.book_table_model import BookTableModel
from ui.search_panel import SearchPanel
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

        # The books are kept in three variables:
        self._books = []         # ORIGINAL order (as scraped). Never changed.
        self._order = []         # ALL books in their current order (original or sorted)
        self._filtered = None    # the matches of the last search; None = no filter

        self._sort_thread = None
        self._sort_on_filtered = False      # which scope the running sort uses
        self._benchmark_thread = None
        self._benchmark_column = ""
        self._benchmark_count = 0

        self.search_panel = SearchPanel()
        self.search_panel.search_requested.connect(self._start_search)
        self.search_panel.clear_requested.connect(self._clear_search)

        self.sort_panel = SortPanel()
        self.sort_panel.sort_requested.connect(self._start_sort)
        self.sort_panel.benchmark_requested.connect(self._start_benchmark)
        self.sort_panel.reset_requested.connect(self._reset_order)

        self.table = self._create_table()

        # Count label: bold, slightly larger, with a little padding
        self.count_label = QLabel()
        self.count_label.setStyleSheet(
            "font-size: 15px; font-weight: bold; padding: 4px 2px;")

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.addWidget(self.search_panel)
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
        """Show a new list of books (e.g. after loading or scraping).
        Everything (order, filter, results) starts again from this list."""
        self._books = books
        self._order = books
        self._filtered = None
        self.sort_panel.clear_result()
        self.search_panel.clear_result()
        self._refresh_table()

    def _refresh_table(self):
        """Show the filtered books if a filter is active, otherwise all of them."""
        if self._filtered is None:
            shown = self._order
            self.count_label.setText(f"Showing {len(shown):,} books")
        else:
            shown = self._filtered
            self.count_label.setText(f"Showing {len(shown):,} of "
                                     f"{len(self._order):,} books (filtered)")
        self.model.set_books(shown)

    # ---------- searching ----------
    def _start_search(self, algorithm_name, column, operator, text):
        """Search ALL books in their current order (so binary search works
        when the books are sorted by the searched column)."""
        if not self._order:
            self.search_panel.show_status("No books loaded yet.")
            return
        try:
            condition = make_condition(column, operator, text)
            result = run_search(algorithm_name, self._order, condition)
        except ValueError as error:          # invalid input, or list not sorted
            self.search_panel.show_status(str(error))
            return
        self._filtered = result.matches
        self._refresh_table()
        self.search_panel.show_result(result, len(self._order))

    def _clear_search(self):
        self._filtered = None
        self._refresh_table()
        self.search_panel.clear_result()

    # ---------- which books to sort or benchmark ----------
    def _books_for_scope(self):
        """The list chosen by the Scope dropdown, or None (with a message)
        if there is nothing to work on."""
        if self.sort_panel.use_filtered_results():
            if self._filtered is None:
                self.sort_panel.show_status(
                    "No filter is active. Search first, or choose 'Full dataset'.")
                return None
            books = self._filtered
        else:
            books = self._books            # every sort starts from the original order
        if not books:
            self.sort_panel.show_status("There are no books to sort.")
            return None
        return books

    # ---------- sorting ----------
    def _start_sort(self, algorithm_name, column, descending):
        books = self._books_for_scope()
        if books is None:
            return
        self._sort_on_filtered = self.sort_panel.use_filtered_results()
        self.sort_panel.set_busy(True)
        # The sort runs in a helper process so the window stays responsive
        self._sort_thread = SortThread(algorithm_name, books, column, descending)
        self._sort_thread.sort_finished.connect(self._on_sort_finished)
        self._sort_thread.sort_failed.connect(self._on_sort_failed)
        self._sort_thread.start()

    def _on_sort_finished(self, result):
        if self._sort_on_filtered:
            self._filtered = result.sorted_books     # only the matches are reordered
        else:
            self._order = result.sorted_books        # the whole list is reordered...
            self._filtered = None                    # ...and the filter is cleared
            self.search_panel.clear_result()
        self._refresh_table()
        self.sort_panel.show_result(result)
        self.sort_panel.set_busy(False)

    def _on_sort_failed(self, message):
        self.sort_panel.set_busy(False)
        self.sort_panel.show_status(f"Sort failed: {message}")

    def _reset_order(self):
        """Original order again, and no filter."""
        self._order = self._books
        self._filtered = None
        self._refresh_table()
        self.sort_panel.clear_result()
        self.search_panel.clear_result()

    # ---------- benchmark ----------
    def _start_benchmark(self, column):
        books = self._books_for_scope()
        if books is None:
            return
        self._benchmark_column = column
        self._benchmark_count = len(books)
        self.sort_panel.set_busy(True)
        self._benchmark_thread = BenchmarkThread(books, column)
        self._benchmark_thread.progress.connect(self._on_benchmark_progress)
        self._benchmark_thread.benchmark_finished.connect(self._on_benchmark_finished)
        self._benchmark_thread.benchmark_failed.connect(self._on_benchmark_failed)
        self._benchmark_thread.start()

    def _on_benchmark_progress(self, position, total, name):
        self.sort_panel.show_status(
            f"Benchmarking: {name} ({position}/{total})... please wait")

    def _on_benchmark_finished(self, results):
        self.sort_panel.set_busy(False)
        BenchmarkDialog(self._benchmark_column, self._benchmark_count,
                        results, self).exec_()

    def _on_benchmark_failed(self, message):
        self.sort_panel.set_busy(False)
        self.sort_panel.show_status(f"Benchmark failed: {message}")

    def finish_sort(self):
        """Wait for background work to end (called when the window closes)."""
        if self._sort_thread is not None and self._sort_thread.isRunning():
            self._sort_thread.wait()
        if self._benchmark_thread is not None and self._benchmark_thread.isRunning():
            self._benchmark_thread.stop()    # stops after the current algorithm
            self._benchmark_thread.wait()
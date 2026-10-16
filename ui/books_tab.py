"""Books tab: displays the books in a table.

Later phases will add sorting and searching controls above the table.
"""
from PyQt5.QtWidgets import (QAbstractItemView, QHeaderView, QLabel,
                             QTableView, QVBoxLayout, QWidget)

from core.book import Book
from ui.book_table_model import BookTableModel

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

        self.table = self._create_table()

        # Count label: bold, slightly larger, with a little padding
        self.count_label = QLabel()
        self.count_label.setStyleSheet(
            "font-size: 15px; font-weight: bold; padding: 4px 2px;")

        # Layout: margins around the edges and spacing between the widgets
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
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
        # NOTE: we do NOT enable Qt's built-in sorting. Sorting must be done
        # by OUR OWN algorithms (Phase 2), not by Qt.

        # Column sizing: the title column stretches to take ALL leftover width,
        # so the table always fills the window. Every other column starts at a
        # fixed width, and the user can still drag their borders to resize.
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setMinimumSectionSize(60)          # title never shrinks below this
        for position, name in enumerate(Book.column_names()):
            if name == "title":
                header.setSectionResizeMode(position, QHeaderView.Stretch)
            else:
                table.setColumnWidth(position, COLUMN_WIDTHS[name])
        return table

    def show_books(self, books):
        """Display a list of Book objects."""
        self.model.set_books(books)
        self.count_label.setText(f"Showing {len(books):,} books")
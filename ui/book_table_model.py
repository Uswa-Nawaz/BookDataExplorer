"""Table model: tells the table view WHAT to display.

Qt tables use a 'model' that the view asks for data on demand. Only the rows
visible on screen are requested, which is why 15,000 rows display instantly.
"""
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from core.book import Book

# Numbers look better right-aligned
NUMERIC_COLUMNS = {"year", "pages", "editions"}


class BookTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._columns = Book.column_names()   # one table column per attribute
        self._books = []                      # the books currently displayed

    def set_books(self, books):
        """Replace the displayed books. The begin/end calls tell the
        view that everything changed so it redraws itself."""
        self.beginResetModel()
        self._books = books
        self.endResetModel()

    # ---------- the 4 methods every table model must provide ----------
    def rowCount(self, parent=QModelIndex()):
        return len(self._books)

    def columnCount(self, parent=QModelIndex()):
        return len(self._columns)

    def data(self, index, role=Qt.DisplayRole):
        """Return what to show in one cell."""
        if not index.isValid():
            return None
        column = self._columns[index.column()]
        book = self._books[index.row()]

        if role == Qt.DisplayRole:
            return str(book.get(column))
        if role == Qt.TextAlignmentRole and column in NUMERIC_COLUMNS:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Column titles on top; row numbers (1, 2, 3...) on the left."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._columns[section].capitalize()
        return super().headerData(section, orientation, role)
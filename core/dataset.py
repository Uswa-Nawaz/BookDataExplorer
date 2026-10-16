"""Dataset: the container that holds every scraped Book.

Books are kept in a plain Python list. This is deliberate: our own
sorting and searching algorithms will work directly on lists.
"""
import csv
import os

from core.book import Book


class Dataset:
    def __init__(self):
        self._books = []   # the list of Book objects

    # ---------- adding / removing ----------
    def add(self, book):
        """Add one book."""
        self._books.append(book)

    def add_many(self, books):
        """Add a list of books at once."""
        self._books.extend(books)

    def clear(self):
        """Remove all books."""
        self._books.clear()

    # ---------- reading ----------
    def __len__(self):
        """Lets us write len(dataset) to get the number of books."""
        return len(self._books)

    def get_all(self):
        """Return a COPY of the book list, so outside code
        (e.g. a sort) cannot accidentally change the stored data."""
        return list(self._books)

    def get_column(self, column):
        """Return the values of one column as a list."""
        return [book.get(column) for book in self._books]

    # ---------- saving / loading (CSV) ----------
    def save_csv(self, path):
        """Save all books to a CSV file so scraped data is not lost."""
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)   # create the folder if missing

        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(Book.column_names())   # header row
            for book in self._books:
                writer.writerow(book.to_row())

    def load_csv(self, path):
        """Replace the current books with the ones stored in a CSV file."""
        self._books.clear()
        with open(path, "r", newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):       # each row -> dictionary
                self._books.append(Book.from_dict(row))
"""The Book entity: one scraped book with 8 attributes."""
from dataclasses import dataclass, fields


@dataclass
class Book:
    # --- 5 text attributes ---
    title: str
    author: str
    genre: str
    publisher: str
    language: str
    # --- 3 numeric attributes ---
    year: int        # first publication year
    pages: int       # number of pages
    editions: int    # number of editions published (a popularity measure)

    @staticmethod
    def column_names():
        """Return the attribute names in order, e.g. ['title', 'author', ...].
        These become the table columns in the UI later."""
        return [f.name for f in fields(Book)]

    def numeric_column_names():
        """Names of the numeric columns (year, pages, editions), found
        from the type of each attribute."""
        return [f.name for f in fields(Book) if f.type in (int, float)]

    def get(self, column):
        """Return this book's value for a column name.
        The sorting and searching code will use this to read any column."""
        return getattr(self, column)

    def to_row(self):
        """Return all values as a list (used when saving to CSV)."""
        return [self.get(name) for name in Book.column_names()]

    @staticmethod
    def from_dict(data):
        """Build a Book from a dictionary of strings (used when loading CSV,
        where every value comes back as text and needs converting)."""
        return Book(
            title=data["title"],
            author=data["author"],
            genre=data["genre"],
            publisher=data["publisher"],
            language=data["language"],
            year=int(data["year"]),
            pages=int(data["pages"]),
            editions=int(data["editions"]),
        )
import csv
import os

COLUMNS = [
    "work_id", "title", "author", "first_publish_year", "pages",
    "edition_count", "ratings_count", "want_to_read_count",
    "publisher", "main_subject", "language_count",
]
NUMERIC_COLUMNS = {
    "first_publish_year", "pages", "edition_count",
    "ratings_count", "want_to_read_count", "language_count",
}

DEFAULT_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "books.csv"
)


class DataManager:
    """Loads books.csv and keeps all rows in memory as dicts.
    Numeric columns are stored as ints so sorting/filtering needs no conversion."""

    def __init__(self, csv_path=DEFAULT_CSV):
        self.csv_path = csv_path
        self.rows = []

    def load(self):
        rows = []
        with open(self.csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                try:
                    for col in NUMERIC_COLUMNS:
                        row[col] = int(row[col])
                except (ValueError, TypeError):
                    continue   # skip a half-written line if the scraper is mid-write
                rows.append(row)
        self.rows = rows
        return len(rows)

    @staticmethod
    def is_numeric(column):
        return column in NUMERIC_COLUMNS
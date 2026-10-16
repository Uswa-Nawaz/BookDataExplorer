"""Temporary test for Step 1B. Run:  python test_dataset.py"""
import os

from core.book import Book
from core.dataset import Dataset

TEST_FILE = os.path.join("data", "test_books.csv")

# 1. Create a dataset and add books (one by one, then several at once)
dataset = Dataset()
dataset.add(Book("Dune", "Frank Herbert", "Sci-Fi", "Chilton", "English", 1965, 412, 120))
dataset.add_many([
    Book("Emma", "Jane Austen", "Romance", "John Murray", "English", 1815, 474, 90),
    Book("Godaan", "Premchand", "Fiction", "Saraswati Press", "Hindi", 1936, 336, 15),
])
print("Books in dataset:", len(dataset))
assert len(dataset) == 3

# 2. Column names and column extraction
print("Columns:", Book.column_names())
assert len(Book.column_names()) == 8
print("Titles:", dataset.get_column("title"))
print("Years:", dataset.get_column("year"))

# 3. get_all returns a copy, so changing it must not affect the dataset
copy = dataset.get_all()
copy.clear()
assert len(dataset) == 3
print("get_all() copy is safe: dataset still has", len(dataset), "books")

# 4. Save to CSV, load into a NEW dataset, and compare
dataset.save_csv(TEST_FILE)
reloaded = Dataset()
reloaded.load_csv(TEST_FILE)
assert reloaded.get_all() == dataset.get_all()
assert isinstance(reloaded.get_all()[0].year, int)       # numbers restored as numbers
assert isinstance(reloaded.get_all()[0].editions, int)
print("Saved and reloaded:", len(reloaded), "books, identical to the original")

# 5. Clear
dataset.clear()
assert len(dataset) == 0
print("After clear():", len(dataset), "books")

os.remove(TEST_FILE)   # clean up the test file
print("\nAll Step 1B checks passed.")
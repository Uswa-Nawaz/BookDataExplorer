"""Test for the searching engine. Run:  python test_searching.py"""
import os

from algorithms.searching import SEARCH_ALGORITHMS, make_condition, run_search
from algorithms.sorting import run_sort
from core.book import Book
from core.dataset import Dataset


def books_from_years(years):
    return [Book(f"Book {i}", "X", "G", "P", "eng", y, 100, 1)
            for i, y in enumerate(years)]


def books_from_titles(titles):
    return [Book(t, "X", "G", "P", "eng", 2000, 100, 1) for t in titles]


def search_both(books, column, operator, text):
    """Run both algorithms; their matches must be identical."""
    condition = make_condition(column, operator, text)
    linear = run_search("Linear Search", books, condition)
    binary = run_search("Binary Search", books, condition)
    assert linear.matches == binary.matches, f"{column} {operator} {text}: results differ"
    return linear, binary


# ---------- Test 1: exact counts on a tiny sorted list ----------
print("TEST 1: numbers in a sorted list of 6 books (years 1, 2, 2, 3, 5, 8)")
years_books = books_from_years([1, 2, 2, 3, 5, 8])
cases = [   # (operator, value, matches, binary comparisons)
    ("equals", "2", 2, 6),
    ("equals", "5", 1, 6),
    ("equals", "4", 0, 6),
    ("greater than", "3", 2, 3),
    ("greater or equal", "5", 2, 3),
    ("less than", "3", 3, 3),
    ("less or equal", "2", 3, 3),
]
for operator, text, match_count, binary_comparisons in cases:
    linear, binary = search_both(years_books, "year", operator, text)
    assert len(linear.matches) == match_count
    assert linear.comparisons == 6                 # linear checks all 6 books
    assert binary.comparisons == binary_comparisons
    print(f"  year {operator} {text:<2}: {match_count} matches | "
          f"linear {linear.comparisons} comparisons, binary {binary.comparisons}  OK")

# ---------- Test 2: text filters ----------
print("\nTEST 2: text filters on 6 titles (apple, apricot, banana, band, bandana, cherry)")
title_books = books_from_titles(["Apple", "apricot", "Banana", "band", "Bandana", "cherry"])
text_cases = [   # (operator, text, matches, binary comparisons)
    ("starts with", "ban", 3, 7),
    ("starts with", "BAN", 3, 7),      # upper/lower case does not matter
    ("equals", "band", 1, 6),
]
for operator, text, match_count, binary_comparisons in text_cases:
    linear, binary = search_both(title_books, "title", operator, text)
    assert len(linear.matches) == match_count
    assert linear.comparisons == 6
    assert binary.comparisons == binary_comparisons
    print(f"  title {operator} '{text}': {match_count} matches | "
          f"linear {linear.comparisons} comparisons, binary {binary.comparisons}  OK")

for operator, text, match_count in [("contains", "an", 3), ("ends with", "na", 2)]:
    result = run_search("Linear Search", title_books, make_condition("title", operator, text))
    assert len(result.matches) == match_count
    print(f"  title {operator} '{text}': {match_count} matches | linear only  OK")

# ---------- Test 3: errors are clear ----------
print("\nTEST 3: invalid input is refused")
refusals = {
    "text in a number column": lambda: make_condition("year", "equals", "abc"),
    "text operator on a number column": lambda: make_condition("year", "contains", "20"),
    "number operator on a text column": lambda: make_condition("title", "greater than", "a"),
    "empty value": lambda: make_condition("title", "contains", "  "),
    "binary search with 'contains'": lambda: run_search(
        "Binary Search", title_books, make_condition("title", "contains", "an")),
    "binary search on unsorted books": lambda: run_search(
        "Binary Search", books_from_years([3, 1, 2]), make_condition("year", "equals", "1")),
}
for label, action in refusals.items():
    try:
        action()
        raise AssertionError(f"{label}: should have been refused")
    except ValueError as error:
        print(f"  {label}: {error}")

# ---------- Test 4: real data ----------
csv_path = os.path.join("data", "books.csv")
if not os.path.exists(csv_path):
    print("\ndata/books.csv not found - test 4 skipped")
else:
    dataset = Dataset()
    dataset.load_csv(csv_path)
    all_books = dataset.get_all()
    print(f"\nTEST 4: {len(all_books):,} real books")
    print(f"  {'Search':<30} {'Algorithm':<14} {'Time (ms)':>9} {'Comparisons':>12} {'Matches':>8}")

    def show(label, result):
        print(f"  {label:<30} {result.algorithm:<14} {result.time_ms:>9.3f} "
              f"{result.comparisons:>12,} {len(result.matches):>8,}")

    # Numbers: sort by year first (with our own merge sort), then search both ways
    by_year = run_sort("Merge Sort", all_books, "year").sorted_books
    for operator in ("equals", "greater than", "less than",
                     "greater or equal", "less or equal"):
        linear, binary = search_both(by_year, "year", operator, "2000")
        assert linear.comparisons == len(all_books)
        assert binary.comparisons <= 30            # about log2(15,000) per bound
        show(f"year {operator} 2000", linear)
        show("", binary)

    # Text: sorted by title, starts with / equals
    by_title = run_sort("Merge Sort", all_books, "title").sorted_books
    sample_title = all_books[100].title
    for operator, text in (("starts with", "the"), ("equals", sample_title)):
        linear, binary = search_both(by_title, "title", operator, text)
        assert binary.comparisons < linear.comparisons
        show(f"title {operator} '{text[:14]}'", linear)
        show("", binary)

    # Filters only linear search can do (works on the unsorted list too)
    for column, operator, text in (("title", "contains", "war"),
                                   ("author", "ends with", "son"),
                                   ("publisher", "contains", "press")):
        result = run_search("Linear Search", all_books, make_condition(column, operator, text))
        show(f"{column} {operator} '{text}'", result)

print("\nAll searching engine checks passed.")
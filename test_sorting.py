"""Test for the sorting engine. Run:  python test_sorting.py

Python's built-in sorted() is used ONLY here, to check our answers.
"""
import os

from algorithms.sorting import ALGORITHMS, make_key, run_sort
from core.book import Book
from core.dataset import Dataset


def books_from_years(years):
    """Make simple test books that differ only in year (and title 'Book 0', 'Book 1'...)."""
    return [Book(f"Book {i}", "X", "G", "P", "eng", year, 100, 1)
            for i, year in enumerate(years)]


def is_sorted(books, column):
    keys = [make_key(b.get(column)) for b in books]
    return keys == sorted(keys)


# ---------- Test 1: exact counts on tiny inputs we can verify by hand ----------
print("TEST 1: comparisons / swaps on 5 items")
expected = {   # (comparisons, swaps) for [5,4,3,2,1] and [1,2,3,4,5]
    "Bubble Sort":    {"reversed": (10, 10), "sorted": (4, 0)},
    "Selection Sort": {"reversed": (10, 2),  "sorted": (10, 0)},
    "Insertion Sort": {"reversed": (10, 10), "sorted": (4, 0)},
    "Merge Sort":     {"reversed": (7, 12),  "sorted": (5, 12)},
    "Quick Sort":     {"reversed": (6, 8),   "sorted": (6, 6)},
}
cases = {"reversed": [5, 4, 3, 2, 1], "sorted": [1, 2, 3, 4, 5]}

for name in ALGORITHMS:
    for case, years in cases.items():
        result = run_sort(name, books_from_years(years), "year")
        got = (result.comparisons, result.swaps)
        assert [b.year for b in result.sorted_books] == [1, 2, 3, 4, 5]
        assert got == expected[name][case], f"{name} {case}: got {got}"
        print(f"  {name:<15} {case:<9} comparisons={got[0]:>2}  swaps={got[1]:>2}  OK")

# ---------- Test 2: stability ----------
print("\nTEST 2: stability (years 2, 2, 1 -> 'Book 0' and 'Book 1' are equal)")
for name in ALGORITHMS:
    result = run_sort(name, books_from_years([2, 2, 1]), "year")
    order = [b.title for b in result.sorted_books]
    keeps_order = order.index("Book 0") < order.index("Book 1")
    print(f"  {name:<15} {result.stability:<9} result: {order}")
    assert keeps_order == result.stable, f"{name}: label does not match behaviour"

# ---------- Tests 3 and 4 use the real data ----------
csv_path = os.path.join("data", "books.csv")
if not os.path.exists(csv_path):
    print("\ndata/books.csv not found - tests 3 and 4 skipped")
else:
    dataset = Dataset()
    dataset.load_csv(csv_path)

    # ---------- Test 3: first 1000 real books ----------
    print("\nTEST 3: first 1000 real books")
    books = dataset.get_all()[:1000]

    for column in ("title", "year"):
        print(f"\n  Sorting by '{column}':")
        print(f"  {'Algorithm':<15} {'Time (ms)':>10} {'Comparisons':>12} "
              f"{'Swaps':>9}  {'Complexity':<10} Stability")
        reference = sorted(books, key=lambda b: make_key(b.get(column)))
        results = {}

        for name in ALGORITHMS:
            r = run_sort(name, books, column)
            assert is_sorted(r.sorted_books, column), f"{name} did not sort correctly"
            if r.stable:   # a stable sort must match Python's (stable) sorted() exactly
                assert r.sorted_books == reference, f"{name} is not stable"
            results[name] = r
            print(f"  {r.algorithm:<15} {r.time_ms:>10.2f} {r.comparisons:>12,} "
                  f"{r.swaps:>9,}  {r.complexity:<10} {r.stability}")

        # Bubble swaps and insertion shifts both equal the number of inversions
        assert results["Bubble Sort"].swaps == results["Insertion Sort"].swaps
        # n log n algorithms need far fewer comparisons than the n^2 ones
        assert results["Merge Sort"].comparisons < 10_000
        assert results["Quick Sort"].comparisons < 100_000

    assert len(books) == 1000   # the original list was never modified

    # ---------- Test 4: all 15,000 books, input ALREADY sorted ----------
    print("\nTEST 4: all books, already-sorted input (the case that breaks "
          "a naive quick sort)")
    all_books = dataset.get_all()
    for column in ("year", "genre"):
        presorted = run_sort("Merge Sort", all_books, column).sorted_books
        for name in ("Merge Sort", "Quick Sort"):
            r = run_sort(name, presorted, column)
            assert is_sorted(r.sorted_books, column), f"{name} failed on {column}"
            print(f"  {column:<6} {name:<11} {r.time_ms:>9.1f} ms "
                  f"{r.comparisons:>11,} comparisons {r.swaps:>11,} swaps")

print("\nAll sorting engine checks passed.")
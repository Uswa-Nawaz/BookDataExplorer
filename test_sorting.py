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


# ---------- Test 1: exact counts on tiny inputs we can verify by hand ----------
print("TEST 1: comparisons / swaps on 5 items")
expected = {   # (comparisons, swaps) for [5,4,3,2,1] and [1,2,3,4,5]
    "Bubble Sort":    {"reversed": (10, 10), "sorted": (4, 0)},
    "Selection Sort": {"reversed": (10, 2),  "sorted": (10, 0)},
    "Insertion Sort": {"reversed": (10, 10), "sorted": (4, 0)},
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

# ---------- Test 3: real data from data/books.csv ----------
print("\nTEST 3: first 1000 real books")
csv_path = os.path.join("data", "books.csv")
if not os.path.exists(csv_path):
    print("  data/books.csv not found - skipped")
else:
    dataset = Dataset()
    dataset.load_csv(csv_path)
    books = dataset.get_all()[:1000]

    for column in ("title", "year"):
        print(f"\n  Sorting by '{column}':")
        print(f"  {'Algorithm':<15} {'Time (ms)':>10} {'Comparisons':>12} "
              f"{'Swaps':>9}  {'Complexity':<9} Stability")
        reference = sorted(books, key=lambda b: make_key(b.get(column)))
        swaps_seen = {}

        for name in ALGORITHMS:
            r = run_sort(name, books, column)
            keys = [make_key(b.get(column)) for b in r.sorted_books]
            assert keys == sorted(keys), f"{name} did not sort correctly"
            if r.stable:   # a stable sort must match Python's (stable) sorted() exactly
                assert r.sorted_books == reference, f"{name} is not stable"
            swaps_seen[name] = r.swaps
            print(f"  {r.algorithm:<15} {r.time_ms:>10.2f} {r.comparisons:>12,} "
                  f"{r.swaps:>9,}  {r.complexity:<9} {r.stability}")

        # Bubble swaps and insertion shifts both equal the number of inversions
        assert swaps_seen["Bubble Sort"] == swaps_seen["Insertion Sort"]

    assert len(books) == 1000   # the original list was never modified

print("\nAll sorting engine checks passed.")
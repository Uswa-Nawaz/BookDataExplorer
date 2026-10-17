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
    "Bubble Sort":       {"reversed": (10, 10), "sorted": (4, 0)},
    "Selection Sort":    {"reversed": (10, 2),  "sorted": (10, 0)},
    "Insertion Sort":    {"reversed": (10, 10), "sorted": (4, 0)},
    "Merge Sort":        {"reversed": (7, 12),  "sorted": (5, 12)},
    "Quick Sort":        {"reversed": (6, 8),   "sorted": (6, 6)},
    "Hybrid Merge Sort": {"reversed": (10, 10), "sorted": (4, 0)},   # n=16: all insertion
    "Shell Sort":        {"reversed": (8, 4),   "sorted": (7, 0)},
    "Heap Sort":         {"reversed": (10, 8),  "sorted": (12, 10)},
}
cases = {"reversed": [5, 4, 3, 2, 1], "sorted": [1, 2, 3, 4, 5]}

for name in ALGORITHMS:
    for case, years in cases.items():
        result = run_sort(name, books_from_years(years), "year")
        got = (result.comparisons, result.swaps)
        assert [b.year for b in result.sorted_books] == [1, 2, 3, 4, 5]
        assert got == expected[name][case], f"{name} {case}: got {got}"
        print(f"  {name:<18} {case:<9} comparisons={got[0]:>2}  swaps={got[1]:>2}  OK")

# Hybrid merge sort with n=2 really splits and merges (5 items)
print("\n  Hybrid Merge Sort with n=2 (small pieces insertion sorted, then merged):")
expected_n2 = {"reversed": (7, 10), "sorted": (5, 8)}
for case, years in cases.items():
    result = run_sort("Hybrid Merge Sort", books_from_years(years), "year", n=2)
    got = (result.comparisons, result.swaps)
    assert [b.year for b in result.sorted_books] == [1, 2, 3, 4, 5]
    assert got == expected_n2[case], f"hybrid n=2 {case}: got {got}"
    print(f"  {'Hybrid (n=2)':<18} {case:<9} comparisons={got[0]:>2}  swaps={got[1]:>2}  OK")

# ---------- Test 2: stability ----------
# An unstable algorithm is not guaranteed to misorder equal items on every
# input, so we try two inputs. 'Book 0' and 'Book 1' have equal years.
print("\nTEST 2: stability (equal items: does 'Book 0' stay before 'Book 1'?)")
stability_inputs = [[2, 2, 1], [2, 2, 1, 3]]
for name in ALGORITHMS:
    keeps_order = True
    for years in stability_inputs:
        result = run_sort(name, books_from_years(years), "year")
        order = [b.title for b in result.sorted_books]
        if order.index("Book 0") > order.index("Book 1"):
            keeps_order = False
    print(f"  {name:<18} {result.stability:<9} equal items kept in order: {keeps_order}")
    if result.stable:
        assert keeps_order, f"{name} is labelled stable but changed the order"
    else:
        assert not keeps_order, f"{name}: expected to show instability here"

# ---------- Tests 3, 4 and 5 use the real data ----------
csv_path = os.path.join("data", "books.csv")
if not os.path.exists(csv_path):
    print("\ndata/books.csv not found - tests 3, 4 and 5 skipped")
else:
    dataset = Dataset()
    dataset.load_csv(csv_path)

    # ---------- Test 3: first 1000 real books ----------
    print("\nTEST 3: first 1000 real books")
    books = dataset.get_all()[:1000]

    for column in ("title", "year"):
        print(f"\n  Sorting by '{column}':")
        print(f"  {'Algorithm':<18} {'Time (ms)':>10} {'Comparisons':>12} "
              f"{'Swaps':>9}  {'Complexity':<10} Stability")
        reference = sorted(books, key=lambda b: make_key(b.get(column)))
        results = {}

        for name in ALGORITHMS:
            r = run_sort(name, books, column)
            assert is_sorted(r.sorted_books, column), f"{name} did not sort correctly"
            if r.stable:   # a stable sort must match Python's (stable) sorted() exactly
                assert r.sorted_books == reference, f"{name} is not stable"
            results[name] = r
            print(f"  {r.algorithm:<18} {r.time_ms:>10.2f} {r.comparisons:>12,} "
                  f"{r.swaps:>9,}  {r.complexity:<10} {r.stability}")

        # Bubble swaps and insertion shifts both equal the number of inversions
        assert results["Bubble Sort"].swaps == results["Insertion Sort"].swaps
        # n log n algorithms need far fewer comparisons than the n^2 ones
        assert results["Merge Sort"].comparisons < 10_000
        assert results["Quick Sort"].comparisons < 100_000
        assert results["Heap Sort"].comparisons < 100_000
        assert results["Shell Sort"].comparisons < 100_000

    assert len(books) == 1000   # the original list was never modified

    # ---------- Test 4: all 15,000 books, input ALREADY sorted ----------
    print("\nTEST 4: all books, already-sorted input")
    all_books = dataset.get_all()
    for column in ("year", "genre"):
        presorted = run_sort("Merge Sort", all_books, column).sorted_books
        for name in ("Merge Sort", "Hybrid Merge Sort", "Shell Sort",
                     "Heap Sort", "Quick Sort"):
            r = run_sort(name, presorted, column)
            assert is_sorted(r.sorted_books, column), f"{name} failed on {column}"
            print(f"  {column:<6} {name:<18} {r.time_ms:>9.1f} ms "
                  f"{r.comparisons:>11,} comparisons {r.swaps:>11,} swaps")

    # ---------- Test 5: the effect of n in Hybrid Merge Sort ----------
    print("\nTEST 5: Hybrid Merge Sort, all books sorted by 'year', different n")
    reference = sorted(all_books, key=lambda b: make_key(b.get("year")))
    merge = run_sort("Merge Sort", all_books, "year")
    print(f"  {'n':>5} {'Time (ms)':>10} {'Comparisons':>12} {'Swaps':>11}")
    for n in (1, 4, 8, 16, 32, 64, 128):
        r = run_sort("Hybrid Merge Sort", all_books, "year", n=n)
        assert r.sorted_books == reference, f"hybrid n={n} is wrong or unstable"
        if n == 1:    # dividing down to single items IS plain merge sort
            assert (r.comparisons, r.swaps) == (merge.comparisons, merge.swaps)
        print(f"  {n:>5} {r.time_ms:>10.1f} {r.comparisons:>12,} {r.swaps:>11,}")

    # n as large as the list means no merging at all: pure insertion sort
    small = dataset.get_all()[:1000]
    hybrid_big_n = run_sort("Hybrid Merge Sort", small, "year", n=1000)
    insertion = run_sort("Insertion Sort", small, "year")
    assert (hybrid_big_n.comparisons, hybrid_big_n.swaps) == \
           (insertion.comparisons, insertion.swaps)
    print("  n=1 matches Merge Sort exactly; n >= list size matches Insertion Sort exactly")

print("\nAll sorting engine checks passed.")
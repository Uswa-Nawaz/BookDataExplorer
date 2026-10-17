"""Test for multi-level sorting. Run:  python test_multisort.py

Python's built-in sorted() is used ONLY here, to check our answers.
"""
import os

from algorithms.sorting import (ALGORITHMS, describe_levels, run_multi_sort,
                                run_sort)
from core.book import Book
from core.dataset import Dataset

COMPARISON_ALGORITHMS = [name for name, a in ALGORITHMS.items() if not a.numeric_only]


def make_books(specs):
    """specs: (genre, year). Books are called 'Book 0', 'Book 1'..."""
    return [Book(f"Book {i}", "X", genre, "P", "eng", year, 100, 1)
            for i, (genre, year) in enumerate(specs)]


def pairs(books):
    return [(b.genre.lower(), b.year) for b in books]


# ---------- Test 1: genre ascending, then year descending ----------
print("TEST 1: 6 books, sort by genre ascending, then year descending")
books = make_books([("Romance", 2001), ("Fantasy", 2005), ("Fantasy", 1990),
                    ("Romance", 1985), ("Fantasy", 2005), ("Mystery", 2015)])
levels = [("genre", False), ("year", True)]
expected_pairs = [("fantasy", 2005), ("fantasy", 2005), ("fantasy", 1990),
                  ("mystery", 2015), ("romance", 2001), ("romance", 1985)]
expected_stable_order = [1, 4, 2, 5, 0, 3]     # Book numbers

for name in COMPARISON_ALGORITHMS:
    result = run_multi_sort(name, books, levels)
    order = [int(b.title.split()[1]) for b in result.sorted_books]
    assert pairs(result.sorted_books) == expected_pairs, f"{name}: wrong order"
    if result.stable:       # equal books (Book 1 and Book 4) must keep their order
        assert order == expected_stable_order, f"{name}: not stable"
    print(f"  {name:<18} {result.stability:<9} books in order: {order}  OK")

assert describe_levels(levels) == "genre ascending, then year descending"
print(f"  levels described as: {describe_levels(levels)}")

# ---------- Test 2: refusals ----------
print("\nTEST 2: invalid requests are refused")
for label, action in {
    "numeric-only algorithm": lambda: run_multi_sort("Counting Sort", books, levels),
    "no levels": lambda: run_multi_sort("Merge Sort", books, []),
}.items():
    try:
        action()
        raise AssertionError(f"{label}: should have been refused")
    except ValueError as error:
        print(f"  {label}: {error}")

# ---------- Tests 3 to 5 use the real data ----------
csv_path = os.path.join("data", "books.csv")
if not os.path.exists(csv_path):
    print("\ndata/books.csv not found - tests 3 to 5 skipped")
else:
    dataset = Dataset()
    dataset.load_csv(csv_path)
    all_books = dataset.get_all()
    small = all_books[:1000]

    # ---------- Test 3: ONE level must behave exactly like a normal sort ----------
    print("\nTEST 3: one level gives the same order and counts as a normal sort (1000 books)")
    for name in COMPARISON_ALGORITHMS:
        multi = run_multi_sort(name, small, [("year", False)])
        single = run_sort(name, small, "year")
        assert multi.sorted_books == single.sorted_books, f"{name}: order differs"
        assert (multi.comparisons, multi.swaps) == (single.comparisons, single.swaps)
    print("  all 8 algorithms: identical order, comparisons and swaps  OK")

    # ---------- Test 4: three levels on 1000 books ----------
    print("\nTEST 4: genre ascending, year descending, title ascending (1000 books)")
    levels = [("genre", False), ("year", True), ("title", False)]

    def sort_key(b):
        return (b.genre.lower(), -b.year, b.title.lower())

    reference = sorted(small, key=sort_key)
    print(f"  {'Algorithm':<18} {'Time (ms)':>10} {'Comparisons':>12} {'Swaps':>9}  Stability")
    for name in COMPARISON_ALGORITHMS:
        r = run_multi_sort(name, small, levels)
        assert [sort_key(b) for b in r.sorted_books] == [sort_key(b) for b in reference]
        if r.stable:
            assert r.sorted_books == reference, f"{name} is not stable"
        print(f"  {r.algorithm:<18} {r.time_ms:>10.2f} {r.comparisons:>12,} "
              f"{r.swaps:>9,}  {r.stability}")
    assert len(small) == 1000        # the original list was never modified

    # ---------- Test 5: the same on all 15,000 books (fast algorithms) ----------
    print(f"\nTEST 5: the same three levels on all {len(all_books):,} books")
    reference_keys = [sort_key(b) for b in sorted(all_books, key=sort_key)]
    for name in ("Merge Sort", "Hybrid Merge Sort", "Quick Sort", "Shell Sort", "Heap Sort"):
        r = run_multi_sort(name, all_books, levels)
        assert [sort_key(b) for b in r.sorted_books] == reference_keys, f"{name} wrong"
        print(f"  {r.algorithm:<18} {r.time_ms:>9.1f} ms {r.comparisons:>11,} comparisons "
              f"{r.swaps:>11,} swaps")

print("\nAll multi-level sorting checks passed.")
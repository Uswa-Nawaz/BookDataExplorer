"""Sorting engine: our own sorting algorithms, all measured the same way.

How sorting works here
----------------------
1. A sort is requested for one column (e.g. "year").
2. We build a list of "entries": (key, book) pairs, where key is the value of
   that column. The algorithms compare ONLY the keys (entry[0]).
3. The algorithm sorts the entries in place and counts its own work in a
   Metrics object.
4. run_sort() times it and packs everything into a SortResult.

What the counters mean
----------------------
comparisons: every time two keys are compared with < or >.
swaps:       every time an element is exchanged with another, or shifted to a
             new position (insertion sort). For insertion sort each shift
             equals one adjacent swap, so the count is the same either way.
"""
import time
from dataclasses import dataclass

from algorithms.metrics import Metrics, SortResult


# ---------------------------------------------------------------------------
# Helper: build the sort key for a value
# ---------------------------------------------------------------------------
def make_key(value):
    """Text is compared in lowercase so 'apple' sorts before 'Zebra'.
    Numbers are used as they are."""
    return value.lower() if isinstance(value, str) else value


# ---------------------------------------------------------------------------
# The algorithms. Each one sorts `entries` in place (ascending by entry[0])
# and updates metrics.comparisons / metrics.swaps.
# ---------------------------------------------------------------------------
def bubble_sort(entries, metrics):
    """Repeatedly swap neighbours that are in the wrong order, so the largest
    value 'bubbles' to the end on each pass. Stops early if a pass makes no swap."""
    n = len(entries)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):           # the last i items are already in place
            metrics.comparisons += 1
            if entries[j][0] > entries[j + 1][0]:
                entries[j], entries[j + 1] = entries[j + 1], entries[j]
                metrics.swaps += 1
                swapped = True
        if not swapped:                      # already sorted: stop early
            break


def selection_sort(entries, metrics):
    """Find the smallest remaining item and swap it into the next position."""
    n = len(entries)
    for i in range(n - 1):
        smallest = i
        for j in range(i + 1, n):
            metrics.comparisons += 1
            if entries[j][0] < entries[smallest][0]:
                smallest = j
        if smallest != i:
            entries[i], entries[smallest] = entries[smallest], entries[i]
            metrics.swaps += 1


def insertion_sort(entries, metrics):
    """Take each item and slide it left into its place among the already
    sorted items before it (like sorting playing cards in your hand)."""
    for i in range(1, len(entries)):
        current = entries[i]
        j = i - 1
        while j >= 0:
            metrics.comparisons += 1
            if entries[j][0] > current[0]:
                entries[j + 1] = entries[j]  # shift the bigger item right
                metrics.swaps += 1
                j -= 1
            else:
                break
        entries[j + 1] = current             # drop the item into its gap


# ---------------------------------------------------------------------------
# Registry: one place that lists every algorithm and its properties
# ---------------------------------------------------------------------------
@dataclass
class SortAlgorithm:
    name: str
    function: object    # the function that does the sorting
    complexity: str     # worst-case time complexity
    stable: bool        # does it keep equal items in their original order?


ALGORITHMS = {a.name: a for a in [
    SortAlgorithm("Bubble Sort",    bubble_sort,    "O(n^2)", stable=True),
    SortAlgorithm("Selection Sort", selection_sort, "O(n^2)", stable=False),
    SortAlgorithm("Insertion Sort", insertion_sort, "O(n^2)", stable=True),
]}


# ---------------------------------------------------------------------------
# The function the rest of the app will call
# ---------------------------------------------------------------------------
def run_sort(algorithm_name, books, column):
    """Sort `books` by `column` with the named algorithm.
    The original list is NOT changed. Returns a SortResult."""
    algorithm = ALGORITHMS[algorithm_name]

    # Build (key, book) entries; the caller's list is left untouched
    entries = [(make_key(book.get(column)), book) for book in books]

    metrics = Metrics()
    start = time.perf_counter()
    algorithm.function(entries, metrics)      # the actual sorting
    time_ms = (time.perf_counter() - start) * 1000

    return SortResult(
        algorithm=algorithm.name,
        sorted_books=[book for _, book in entries],
        time_ms=time_ms,
        comparisons=metrics.comparisons,
        swaps=metrics.swaps,
        complexity=algorithm.complexity,
        stable=algorithm.stable,
    )
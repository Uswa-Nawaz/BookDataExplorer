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
swaps:       every time an element is exchanged with another, or moved to a
             new position. Insertion sort counts each shift as one swap (this
             equals one adjacent swap). Merge sort counts each element it
             copies back into the list while merging.
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
    """Insertion sort on the whole list."""
    _insertion_sort_range(entries, 0, len(entries), metrics)


def _insertion_sort_range(entries, low, high, metrics):
    """Take each item in [low, high) and slide it left into its place among
    the already sorted items before it (like sorting playing cards)."""
    for i in range(low + 1, high):
        current = entries[i]
        j = i - 1
        while j >= low:
            metrics.comparisons += 1
            if entries[j][0] > current[0]:
                entries[j + 1] = entries[j]  # shift the bigger item right
                metrics.swaps += 1
                j -= 1
            else:
                break
        entries[j + 1] = current             # drop the item into its gap


def merge_sort(entries, metrics):
    """Split the list in half, sort each half, then merge the two sorted
    halves into one. Works on the range [low, high) of the list."""
    _merge_sort_range(entries, 0, len(entries), metrics)


def _merge_sort_range(entries, low, high, metrics):
    if high - low < 2:                  # 0 or 1 item: already sorted
        return
    middle = (low + high) // 2
    _merge_sort_range(entries, low, middle, metrics)    # sort left half
    _merge_sort_range(entries, middle, high, metrics)   # sort right half
    _merge(entries, low, middle, high, metrics)         # combine them


def _merge(entries, low, middle, high, metrics):
    """Merge the sorted halves [low, middle) and [middle, high).
    Each element written back into `entries` counts as one swap (a move)."""
    left = entries[low:middle]          # temporary copies of the two halves
    right = entries[middle:high]
    i = j = 0
    k = low                             # next position to fill in `entries`

    # Repeatedly take the smaller front item of the two halves
    while i < len(left) and j < len(right):
        metrics.comparisons += 1
        if left[i][0] <= right[j][0]:   # '<=' takes the LEFT item on a tie: stable
            entries[k] = left[i]
            i += 1
        else:
            entries[k] = right[j]
            j += 1
        metrics.swaps += 1
        k += 1

    # One half is used up: copy whatever remains of the other half
    while i < len(left):
        entries[k] = left[i]
        i += 1
        k += 1
        metrics.swaps += 1
    while j < len(right):
        entries[k] = right[j]
        j += 1
        k += 1
        metrics.swaps += 1


def quick_sort(entries, metrics):
    """Pick a pivot, put smaller items on its left and larger on its right,
    then do the same for each side.

    Instead of calling itself, it keeps a to-do list of ranges still to sort.
    This avoids Python's recursion limit on large or already-sorted input."""
    pending = [(0, len(entries) - 1)]   # ranges (low, high) still to sort
    while pending:
        low, high = pending.pop()
        if low >= high:                 # 0 or 1 item: nothing to do
            continue
        pivot_position = _partition(entries, low, high, metrics)
        pending.append((low, pivot_position - 1))       # left side
        pending.append((pivot_position + 1, high))      # right side


def _partition(entries, low, high, metrics):
    """Lomuto partition of entries[low..high] (inclusive).
    Returns the final position of the pivot."""
    # Use the MIDDLE item as pivot: move it to the end first. (A fixed end
    # pivot would be very slow on already-sorted data.)
    middle = (low + high) // 2
    if middle != high:
        entries[middle], entries[high] = entries[high], entries[middle]
        metrics.swaps += 1
    pivot_key = entries[high][0]

    boundary = low      # everything before `boundary` is smaller than the pivot
    for j in range(low, high):
        metrics.comparisons += 1
        if entries[j][0] < pivot_key:
            if j != boundary:
                entries[boundary], entries[j] = entries[j], entries[boundary]
                metrics.swaps += 1
            boundary += 1

    # Put the pivot between the smaller items and the rest
    if boundary != high:
        entries[boundary], entries[high] = entries[high], entries[boundary]
        metrics.swaps += 1
    return boundary

# Class definition: stop dividing once a piece has n items or fewer, then
# sort that small piece with insertion sort. 16 is a common starting value.
HYBRID_THRESHOLD = 16


def hybrid_merge_sort(entries, metrics, n=HYBRID_THRESHOLD):
    """Merge sort that does not divide down to single elements. Pieces of
    size n or smaller are sorted with insertion sort instead."""
    n = max(n, 1)    # n below 1 would divide forever
    _hybrid_range(entries, 0, len(entries), metrics, n)


def _hybrid_range(entries, low, high, metrics, n):
    if high - low <= n:                       # small piece: insertion sort
        _insertion_sort_range(entries, low, high, metrics)
        return
    middle = (low + high) // 2
    _hybrid_range(entries, low, middle, metrics, n)
    _hybrid_range(entries, middle, high, metrics, n)
    _merge(entries, low, middle, high, metrics)   # same merge as Merge Sort


def shell_sort(entries, metrics):
    """Insertion sort that first compares items far apart (a 'gap'), so items
    move long distances early. The gap starts at n/2 and halves until it is 1
    (the last pass is a normal insertion sort on nearly sorted data)."""
    n = len(entries)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            current = entries[i]
            j = i
            while j >= gap:
                metrics.comparisons += 1
                if entries[j - gap][0] > current[0]:
                    entries[j] = entries[j - gap]   # shift the bigger item
                    metrics.swaps += 1
                    j -= gap
                else:
                    break
            entries[j] = current
        gap //= 2


def heap_sort(entries, metrics):
    """Build a max-heap (largest item at the top), then repeatedly swap the
    top item to the end of the list and repair the shrinking heap."""
    n = len(entries)
    for start in range(n // 2 - 1, -1, -1):          # build the heap
        _sift_down(entries, start, n, metrics)
    for end in range(n - 1, 0, -1):                  # extract the largest each time
        entries[0], entries[end] = entries[end], entries[0]
        metrics.swaps += 1
        _sift_down(entries, 0, end, metrics)         # heap is now entries[0:end]


def _sift_down(entries, root, size, metrics):
    """Move entries[root] down until both its children are smaller.
    The heap occupies entries[0:size]; children of i are 2i+1 and 2i+2."""
    while True:
        child = 2 * root + 1
        if child >= size:                            # no children: done
            return
        if child + 1 < size:                         # pick the larger child
            metrics.comparisons += 1
            if entries[child + 1][0] > entries[child][0]:
                child += 1
        metrics.comparisons += 1
        if entries[child][0] > entries[root][0]:
            entries[root], entries[child] = entries[child], entries[root]
            metrics.swaps += 1
            root = child
        else:
            return

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
    SortAlgorithm("Bubble Sort",       bubble_sort,       "O(n^2)",     stable=True),
    SortAlgorithm("Selection Sort",    selection_sort,    "O(n^2)",     stable=False),
    SortAlgorithm("Insertion Sort",    insertion_sort,    "O(n^2)",     stable=True),
    SortAlgorithm("Merge Sort",        merge_sort,        "O(n log n)", stable=True),
    SortAlgorithm("Quick Sort",        quick_sort,        "O(n^2)",     stable=False),
    SortAlgorithm("Hybrid Merge Sort", hybrid_merge_sort, "O(n log n)", stable=True),
    SortAlgorithm("Shell Sort",        shell_sort,        "O(n^2)",     stable=False),
    SortAlgorithm("Heap Sort",         heap_sort,         "O(n log n)", stable=False),
]}

# ---------------------------------------------------------------------------
# The function the rest of the app will call
# ---------------------------------------------------------------------------
def run_sort(algorithm_name, books, column, **options):
    """Sort `books` by `column` with the named algorithm.
    The original list is NOT changed. Returns a SortResult."""
    algorithm = ALGORITHMS[algorithm_name]

    # Build (key, book) entries; the caller's list is left untouched
    entries = [(make_key(book.get(column)), book) for book in books]

    metrics = Metrics()
    start = time.perf_counter()
    algorithm.function(entries, metrics, **options)      # the actual sorting
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
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
             writes back while merging. Counting and radix sort count each
             placement into the output list; bucket sort counts each
             placement into a bucket and each write back.
"""
import time
from dataclasses import dataclass
from core.book import Book
from algorithms.metrics import Metrics, SortResult


# ---------------------------------------------------------------------------
# Helper: build the sort key for a value
# ---------------------------------------------------------------------------
def make_key(value):
    """Text is compared in lowercase so 'apple' sorts before 'Zebra'.
    Numbers are used as they are."""
    return value.lower() if isinstance(value, str) else value

class Descending:
    """Wraps a key so that it sorts in REVERSE order. It reverses every
    comparison, so all our comparison-based algorithms work with it unchanged."""
    __slots__ = ("key",)

    def __init__(self, key):
        self.key = key

    def __eq__(self, other):
        return self.key == other.key

    def __lt__(self, other):
        return self.key > other.key

    def __gt__(self, other):
        return self.key < other.key

    def __le__(self, other):
        return self.key >= other.key

    def __ge__(self, other):
        return self.key <= other.key


def make_multi_key(book, levels):
    """Key for sorting by several columns: a tuple with one part per level.
    levels = [(column, descending), ...]. Python compares tuples part by part,
    so the second part only matters when the first parts are equal."""
    parts = []
    for column, descending in levels:
        key = make_key(book.get(column))
        parts.append(Descending(key) if descending else key)
    return tuple(parts)


def describe_levels(levels):
    """e.g. 'genre ascending, then year descending'"""
    return ", then ".join(f"{column} {'descending' if descending else 'ascending'}"
                          for column, descending in levels)
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
# Non-comparison sorts (numeric columns only: year, pages, editions).
# They sort by the VALUE of each key instead of comparing items with each
# other. Their only key comparisons are the scan that finds the smallest and
# largest key (and, for bucket sort, the insertion sort inside each bucket).
# ---------------------------------------------------------------------------
MAX_COUNTING_RANGE = 10_000_000   # largest key range counting sort will accept


def _find_range(entries, metrics):
    """Return (smallest key, largest key). Each item is compared with the
    current smallest and largest, so each item costs 2 comparisons."""
    low = high = entries[0][0]
    for i in range(1, len(entries)):
        key = entries[i][0]
        metrics.comparisons += 2
        if key < low:
            low = key
        if key > high:
            high = key
    return low, high


def counting_sort(entries, metrics):
    """Count how many items have each key value, turn the counts into final
    positions, then place every item directly into its position."""
    if not entries:
        return
    low, high = _find_range(entries, metrics)
    size = high - low + 1                        # number of possible key values
    if size > MAX_COUNTING_RANGE:
        raise ValueError(f"Counting Sort: key range of {size:,} is too large")

    counts = [0] * size
    for entry in entries:                        # 1. count each key value
        counts[entry[0] - low] += 1
    for i in range(1, size):                     # 2. running totals: counts[i] becomes
        counts[i] += counts[i - 1]               #    the number of items with key <= low + i

    output = [None] * len(entries)
    for entry in reversed(entries):              # 3. place items, starting from the END,
        counts[entry[0] - low] -= 1              #    so equal items keep their order (stable)
        output[counts[entry[0] - low]] = entry
        metrics.swaps += 1
    entries[:] = output                          # copy the result back into the list


def radix_sort(entries, metrics):
    """Sort by one decimal digit at a time, starting from the last digit
    (least significant first). Each pass is a stable counting sort on that digit."""
    if not entries:
        return
    low, high = _find_range(entries, metrics)
    largest = high - low                         # keys are shifted so the smallest is 0
    place = 1                                    # 1 = ones digit, 10 = tens digit, ...
    while largest // place > 0:                  # one pass per digit of the largest key
        _sort_by_digit(entries, low, place, metrics)
        place *= 10


def _sort_by_digit(entries, low, place, metrics):
    """One radix pass: a stable counting sort on a single decimal digit."""
    counts = [0] * 10                            # digits are 0..9
    for entry in entries:
        counts[((entry[0] - low) // place) % 10] += 1
    for digit in range(1, 10):
        counts[digit] += counts[digit - 1]

    output = [None] * len(entries)
    for entry in reversed(entries):              # from the end: keeps the pass stable
        digit = ((entry[0] - low) // place) % 10
        counts[digit] -= 1
        output[counts[digit]] = entry
        metrics.swaps += 1
    entries[:] = output


def bucket_sort(entries, metrics):
    """Spread the items over buckets by key range, sort each bucket with
    insertion sort, then join the buckets in order."""
    if not entries:
        return
    low, high = _find_range(entries, metrics)
    bucket_count = max(1, int(len(entries) ** 0.5))   # about sqrt(n) buckets
    span = high - low + 1                             # number of possible key values

    buckets = [[] for _ in range(bucket_count)]
    for entry in entries:                             # 1. distribute into buckets
        index = (entry[0] - low) * bucket_count // span
        buckets[index].append(entry)                  # order inside a bucket = original order
        metrics.swaps += 1

    position = 0
    for bucket in buckets:                            # 2. sort each bucket, then join
        _insertion_sort_range(bucket, 0, len(bucket), metrics)
        for entry in bucket:
            entries[position] = entry
            position += 1
            metrics.swaps += 1

# ---------------------------------------------------------------------------
# Registry: one place that lists every algorithm and its properties
# ---------------------------------------------------------------------------
@dataclass
class SortAlgorithm:
    name: str
    function: object    # the function that does the sorting
    complexity: str     # worst-case time complexity
    stable: bool        # does it keep equal items in their original order?
    numeric_only: bool = False   # True if it only works on whole-number columns


ALGORITHMS = {a.name: a for a in [
    SortAlgorithm("Bubble Sort",       bubble_sort,       "O(n^2)",      stable=True),
    SortAlgorithm("Selection Sort",    selection_sort,    "O(n^2)",      stable=False),
    SortAlgorithm("Insertion Sort",    insertion_sort,    "O(n^2)",      stable=True),
    SortAlgorithm("Merge Sort",        merge_sort,        "O(n log n)",  stable=True),
    SortAlgorithm("Quick Sort",        quick_sort,        "O(n^2)",      stable=False),
    SortAlgorithm("Hybrid Merge Sort", hybrid_merge_sort, "O(n log n)",  stable=True),
    SortAlgorithm("Shell Sort",        shell_sort,        "O(n^2)",      stable=False),
    SortAlgorithm("Heap Sort",         heap_sort,         "O(n log n)",  stable=False),
    SortAlgorithm("Counting Sort",     counting_sort,     "O(n + k)",    stable=True,  numeric_only=True),
    SortAlgorithm("Radix Sort",        radix_sort,        "O(d(n + k))", stable=True,  numeric_only=True),
    SortAlgorithm("Bucket Sort",       bucket_sort,       "O(n^2)",      stable=True,  numeric_only=True),
]}


def is_available(algorithm_name, column):
    """Can this algorithm sort this column?
    Counting, radix and bucket sort need a numeric column."""
    return (not ALGORITHMS[algorithm_name].numeric_only
            or column in Book.numeric_column_names())

# ---------------------------------------------------------------------------
# The function the rest of the app will call
# ---------------------------------------------------------------------------
def run_sort(algorithm_name, books, column, **options):
    """Sort `books` by `column` with the named algorithm.
    The original list is NOT changed. Returns a SortResult."""
    algorithm = ALGORITHMS[algorithm_name]

    # Build (key, book) entries; the caller's list is left untouched
    entries = [(make_key(book.get(column)), book) for book in books]

    # Counting, radix and bucket sort need whole-number keys
    if algorithm.numeric_only and not all(isinstance(key, int) for key, _ in entries):
        raise ValueError(f"{algorithm.name} only works on numeric columns "
                         "(year, pages, editions)")

    return _sort_entries(algorithm, entries, options)


def run_multi_sort(algorithm_name, books, levels, **options):
    """Sort `books` by several columns. levels = [(column, descending), ...],
    most important first. Returns a SortResult."""
    algorithm = ALGORITHMS[algorithm_name]
    if not levels:
        raise ValueError("Choose at least one column to sort by.")
    if algorithm.numeric_only:
        raise ValueError(f"{algorithm.name} cannot sort by several columns.")

    entries = [(make_multi_key(book, levels), book) for book in books]
    return _sort_entries(algorithm, entries, options)


def _sort_entries(algorithm, entries, options):
    """Time the algorithm on the (key, book) entries and pack the result."""
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
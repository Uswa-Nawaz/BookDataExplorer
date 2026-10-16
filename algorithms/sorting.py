import time

INSERTION_CUTOFF = 16   # hybrid merge sort switches to insertion sort below this size
BUCKET_SMALL = 64       # bucket sort: buckets bigger than this use merge sort inside


class Stats:
    def __init__(self):
        self.comparisons = 0
        self.swaps = 0      # every swap OR element move/shift/placement counts as one


# Each algorithm takes (items, lt, stats) and returns the sorted list.
# items = list of (key, row) pairs. lt(a, b) means "a must come before b";
# it counts comparisons and handles ascending/descending for us.
# The three non-comparison sorts (counting, radix, bucket) use the integer
# key directly, so run_sort() negates keys for them when sorting descending.

def bubble_sort(a, lt, st):
    n = len(a)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            if lt(a[j + 1], a[j]):
                a[j], a[j + 1] = a[j + 1], a[j]
                st.swaps += 1
                swapped = True
        if not swapped:
            break
    return a


def selection_sort(a, lt, st):
    n = len(a)
    for i in range(n - 1):
        m = i
        for j in range(i + 1, n):
            if lt(a[j], a[m]):
                m = j
        if m != i:
            a[i], a[m] = a[m], a[i]
            st.swaps += 1
    return a


def insertion_sort(a, lt, st):
    for i in range(1, len(a)):
        cur = a[i]
        j = i - 1
        while j >= 0 and lt(cur, a[j]):
            a[j + 1] = a[j]
            st.swaps += 1
            j -= 1
        a[j + 1] = cur
    return a


def _merge(left, right, lt, st):
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if lt(right[j], left[i]):      # strict, so equal items keep their order (stable)
            out.append(right[j])
            j += 1
        else:
            out.append(left[i])
            i += 1
        st.swaps += 1
    st.swaps += (len(left) - i) + (len(right) - j)
    out.extend(left[i:])
    out.extend(right[j:])
    return out


def merge_sort(a, lt, st):
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    return _merge(merge_sort(a[:mid], lt, st), merge_sort(a[mid:], lt, st), lt, st)


def hybrid_merge_sort(a, lt, st):
    # Merge sort, but small pieces are sorted with insertion sort (faster in practice).
    if len(a) <= INSERTION_CUTOFF:
        return insertion_sort(a, lt, st)
    mid = len(a) // 2
    return _merge(hybrid_merge_sort(a[:mid], lt, st),
                  hybrid_merge_sort(a[mid:], lt, st), lt, st)


def quick_sort(a, lt, st):
    # Iterative with 3-way partitioning: no recursion limit problems and
    # it copes with many equal keys (e.g. lots of 0 values).
    stack = [(0, len(a) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        pivot = a[(lo + hi) // 2]
        lt_i, i, gt_i = lo, lo, hi
        while i <= gt_i:
            if lt(a[i], pivot):
                a[lt_i], a[i] = a[i], a[lt_i]
                st.swaps += 1
                lt_i += 1
                i += 1
            elif lt(pivot, a[i]):
                a[i], a[gt_i] = a[gt_i], a[i]
                st.swaps += 1
                gt_i -= 1
            else:
                i += 1
        stack.append((lo, lt_i - 1))
        stack.append((gt_i + 1, hi))
    return a


def heap_sort(a, lt, st):
    n = len(a)

    def sift_down(root, end):
        while True:
            child = 2 * root + 1
            if child >= end:
                break
            if child + 1 < end and lt(a[child], a[child + 1]):
                child += 1
            if lt(a[root], a[child]):
                a[root], a[child] = a[child], a[root]
                st.swaps += 1
                root = child
            else:
                break

    for start in range(n // 2 - 1, -1, -1):
        sift_down(start, n)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        st.swaps += 1
        sift_down(0, end)
    return a


def shell_sort(a, lt, st):
    n = len(a)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            cur = a[i]
            j = i
            while j >= gap and lt(cur, a[j - gap]):
                a[j] = a[j - gap]
                st.swaps += 1
                j -= gap
            a[j] = cur
        gap //= 2
    return a


# ---------- non-comparison sorts (integer keys only) ----------
# They never compare two keys with each other, so their comparison count
# is 0. That is normal and worth mentioning in your benchmark discussion.

def counting_sort(a, lt, st):
    if not a:
        return a
    lo = min(k for k, _ in a)
    hi = max(k for k, _ in a)
    count = [0] * (hi - lo + 1)
    for k, _ in a:
        count[k - lo] += 1
    for i in range(1, len(count)):           # prefix sums = final positions
        count[i] += count[i - 1]
    out = [None] * len(a)
    for item in reversed(a):                 # walk backwards to stay stable
        count[item[0] - lo] -= 1
        out[count[item[0] - lo]] = item
        st.swaps += 1
    return out


def radix_sort(a, lt, st):
    # LSD radix sort, base 10: one stable pass per digit.
    if not a:
        return a
    lo = min(k for k, _ in a)
    max_val = max(k for k, _ in a) - lo
    exp = 1
    while max_val // exp > 0:
        buckets = [[] for _ in range(10)]
        for item in a:
            buckets[((item[0] - lo) // exp) % 10].append(item)
            st.swaps += 1
        a = [item for b in buckets for item in b]
        exp *= 10
    return a


def bucket_sort(a, lt, st):
    n = len(a)
    if n <= 1:
        return a
    lo = min(k for k, _ in a)
    hi = max(k for k, _ in a)
    if lo == hi:
        return a
    size = hi - lo + 1
    buckets = [[] for _ in range(n)]
    for item in a:
        buckets[(item[0] - lo) * n // size].append(item)
        st.swaps += 1
    out = []
    for b in buckets:
        if len(b) <= BUCKET_SMALL:
            b = insertion_sort(b, lt, st)    # classic: insertion sort inside a bucket
        else:
            b = merge_sort(b, lt, st)        # skewed data: keep big buckets fast
        out.extend(b)
    return out


ALGORITHMS = {
    "Bubble Sort":       {"func": bubble_sort,       "complexity": "O(n²)",          "stable": True,  "numeric_only": False},
    "Selection Sort":    {"func": selection_sort,    "complexity": "O(n²)",          "stable": False, "numeric_only": False},
    "Insertion Sort":    {"func": insertion_sort,    "complexity": "O(n²)",          "stable": True,  "numeric_only": False},
    "Merge Sort":        {"func": merge_sort,        "complexity": "O(n log n)",     "stable": True,  "numeric_only": False},
    "Hybrid Merge Sort": {"func": hybrid_merge_sort, "complexity": "O(n log n)",     "stable": True,  "numeric_only": False},
    "Quick Sort":        {"func": quick_sort,        "complexity": "O(n log n) avg", "stable": False, "numeric_only": False},
    "Counting Sort":     {"func": counting_sort,     "complexity": "O(n + k)",       "stable": True,  "numeric_only": True},
    "Radix Sort":        {"func": radix_sort,        "complexity": "O(d·(n + b))",   "stable": True,  "numeric_only": True},
    "Bucket Sort":       {"func": bucket_sort,       "complexity": "O(n + k) avg",   "stable": True,  "numeric_only": True},
    "Heap Sort":         {"func": heap_sort,         "complexity": "O(n log n)",     "stable": False, "numeric_only": False},
    "Shell Sort":        {"func": shell_sort,        "complexity": "O(n log² n)",    "stable": False, "numeric_only": False},
}


def run_sort(rows, key_func, algorithm, reverse=False):
    """Sort rows by key_func(row) using the chosen algorithm.
    Returns (sorted_rows, {"time_ms", "comparisons", "swaps"})."""
    info = ALGORITHMS[algorithm]
    st = Stats()

    if info["numeric_only"]:
        # integer keys; negate them to sort descending (still stable)
        sign = -1 if reverse else 1
        items = [(sign * key_func(r), r) for r in rows]

        def lt(x, y):
            st.comparisons += 1
            return x[0] < y[0]
    else:
        items = [(key_func(r), r) for r in rows]

        def lt(x, y):
            st.comparisons += 1
            return x[0] > y[0] if reverse else x[0] < y[0]

    start = time.perf_counter()
    result = info["func"](items, lt, st)
    ms = (time.perf_counter() - start) * 1000

    return [row for _, row in result], {
        "time_ms": round(ms, 2),
        "comparisons": st.comparisons,
        "swaps": st.swaps,
    }


# Quick test:  python algorithms/sorting.py
if __name__ == "__main__":
    import csv
    import os

    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "books.csv")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))[:1500]

    tests = [
        ("pages", lambda r: int(r["pages"]), True),
        ("title", lambda r: r["title"].lower(), False),
    ]
    for col, key, is_num in tests:
        for reverse in (False, True):
            expected = sorted(rows, key=key, reverse=reverse)
            exp_ids = [r["work_id"] for r in expected]
            exp_keys = [key(r) for r in expected]
            print(f"\nSorting {len(rows)} rows by {col} ({'desc' if reverse else 'asc'})")
            print(f"{'Algorithm':<19}{'ms':>10}{'compares':>12}{'swaps':>10}  correct?")
            for name, info in ALGORITHMS.items():
                if info["numeric_only"] and not is_num:
                    print(f"{name:<19}{'(numeric columns only)':>32}")
                    continue
                out, m = run_sort(rows, key, name, reverse)
                if info["stable"]:
                    ok = [r["work_id"] for r in out] == exp_ids   # exact order incl. ties
                else:
                    ok = [key(r) for r in out] == exp_keys
                print(f"{name:<19}{m['time_ms']:>10}{m['comparisons']:>12}{m['swaps']:>10}  {ok}")
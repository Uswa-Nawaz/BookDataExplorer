import math
import time


class Stats:
    def __init__(self):
        self.comparisons = 0


def _collect(keys, start, target, st):
    """From index `start`, gather every consecutive entry equal to target."""
    out = []
    i = start
    while i < len(keys):
        st.comparisons += 1
        if keys[i] != target:
            break
        out.append(i)
        i += 1
    return out


def linear_search(keys, target, st):
    hits = []
    for i, k in enumerate(keys):
        st.comparisons += 1
        if k == target:
            hits.append(i)
    return hits


def binary_search(keys, target, st):          # keys must be sorted
    lo, hi = 0, len(keys)
    while lo < hi:                             # finds the FIRST position >= target
        mid = (lo + hi) // 2
        st.comparisons += 1
        if keys[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return _collect(keys, lo, target, st)


def jump_search(keys, target, st):             # keys must be sorted
    n = len(keys)
    if n == 0:
        return []
    step = max(1, int(math.sqrt(n)))
    prev = 0
    while prev < n:                            # jump block by block
        last = min(prev + step, n) - 1
        st.comparisons += 1
        if keys[last] >= target:
            break
        prev += step
    else:
        return []
    i = prev                                   # linear scan inside that block
    while i < n:
        st.comparisons += 1
        if keys[i] >= target:
            break
        i += 1
    return _collect(keys, i, target, st)


def interpolation_search(keys, target, st):    # sorted NUMERIC keys
    lo, hi = 0, len(keys) - 1
    while lo <= hi and keys[lo] <= target <= keys[hi]:
        st.comparisons += 1
        if keys[hi] == keys[lo]:
            pos = lo
        else:
            pos = lo + (target - keys[lo]) * (hi - lo) // (keys[hi] - keys[lo])
        st.comparisons += 1
        if keys[pos] == target:
            while pos > 0 and keys[pos - 1] == target:   # walk back to the first match
                st.comparisons += 1
                pos -= 1
            return _collect(keys, pos, target, st)
        if keys[pos] < target:
            lo = pos + 1
        else:
            hi = pos - 1
    return []


SEARCH_ALGORITHMS = {
    "Linear Search":        {"func": linear_search,        "complexity": "O(n)",          "needs_sorted": False, "numeric_only": False},
    "Binary Search":        {"func": binary_search,        "complexity": "O(log n)",      "needs_sorted": True,  "numeric_only": False},
    "Jump Search":          {"func": jump_search,          "complexity": "O(√n)",         "needs_sorted": True,  "numeric_only": False},
    "Interpolation Search": {"func": interpolation_search, "complexity": "O(log log n) avg", "needs_sorted": True, "numeric_only": True},
}


def run_search(rows, column, text, algorithm, numeric):
    """Exact-match search (case-insensitive for text).
    Returns (matching_rows, {"time_ms", "comparisons", "index_ms"})."""
    info = SEARCH_ALGORITHMS[algorithm]
    if numeric:
        target = int(text.strip())             # ValueError if not a number
        key = lambda r: r[column]
    else:
        target = text.strip().lower()
        key = lambda r: r[column].lower()

    st = Stats()
    index_ms = None
    order = None
    if info["needs_sorted"]:
        # Binary/jump/interpolation need sorted data, so build a sorted index first.
        # That one-time cost is reported separately from the search time.
        t0 = time.perf_counter()
        pairs = sorted((key(r), i) for i, r in enumerate(rows))
        keys = [k for k, _ in pairs]
        order = [i for _, i in pairs]
        index_ms = (time.perf_counter() - t0) * 1000
    else:
        keys = [key(r) for r in rows]

    t0 = time.perf_counter()
    hits = info["func"](keys, target, st)
    ms = (time.perf_counter() - t0) * 1000

    matches = [rows[order[h]] for h in hits] if order is not None else [rows[h] for h in hits]
    return matches, {"time_ms": ms, "comparisons": st.comparisons, "index_ms": index_ms}
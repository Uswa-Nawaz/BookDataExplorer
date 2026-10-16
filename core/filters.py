import operator
import time

from core.data_manager import DataManager

TEXT_OPS = ["contains", "starts with", "ends with", "equals", "not equals"]
NUM_OPS = ["=", "≠", ">", "≥", "<", "≤"]

_NUM = {"=": operator.eq, "≠": operator.ne, ">": operator.gt,
        "≥": operator.ge, "<": operator.lt, "≤": operator.le}

_TEXT = {
    "contains":    lambda s, t: t in s,
    "starts with": lambda s, t: s.startswith(t),
    "ends with":   lambda s, t: s.endswith(t),
    "equals":      lambda s, t: s == t,
    "not equals":  lambda s, t: s != t,
}


def _prepare(conditions):
    prepared = []
    for c in conditions:
        col = c["column"]
        numeric = DataManager.is_numeric(col)
        if numeric:
            try:
                value = int(c["value"].strip())
            except ValueError:
                raise ValueError(f"'{c['value']}' is not a whole number (column: {col})")
            test = _NUM[c["op"]]
        else:
            value = c["value"].strip().lower()
            test = _TEXT[c["op"]]
        prepared.append((c["connector"], c["negate"], col, test, value, numeric))
    return prepared


def apply_filters(rows, conditions):
    """conditions: list of {connector, negate, column, op, value}.
    Evaluated top to bottom; AND binds tighter than OR (normal precedence).
    Returns (matching_rows, time_ms)."""
    prepared = _prepare(conditions)

    groups = []                       # an OR of AND-groups
    for i, p in enumerate(prepared):
        if i == 0 or p[0] == "OR":
            groups.append([p])
        else:
            groups[-1].append(p)

    def check(row, p):
        _, negate, col, test, value, numeric = p
        v = row[col]
        return test(v if numeric else v.lower(), value) != negate   # != flips it when NOT is ticked

    start = time.perf_counter()
    result = [r for r in rows if any(all(check(r, p) for p in g) for g in groups)]
    return result, (time.perf_counter() - start) * 1000
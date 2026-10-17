"""Searching engine: finds the books that match ONE condition.

A condition has three parts:  column + operator + value
    e.g.  title  starts with  "the"        year  greater than  2000

Two algorithms are provided (more can be added to the registry later):
  Linear Search - checks every book. Works for every column and operator.
  Binary Search - repeatedly halves the list. Much faster, but the books must
                  already be sorted (ascending) by the searched column, and it
                  cannot do 'contains' or 'ends with'.

comparisons = how many times a book's value was tested or compared.
"""
import time
from dataclasses import dataclass

from algorithms.metrics import Metrics
from algorithms.sorting import make_key
from core.book import Book

TEXT_OPERATORS = ["contains", "starts with", "ends with", "equals"]
NUMERIC_OPERATORS = ["equals", "greater than", "less than",
                     "greater or equal", "less or equal"]

# What each operator means: test(book's key, searched value) -> True / False
TESTS = {
    "equals":           lambda key, value: key == value,
    "contains":         lambda key, value: value in key,
    "starts with":      lambda key, value: key.startswith(value),
    "ends with":        lambda key, value: key.endswith(value),
    "greater than":     lambda key, value: key > value,
    "less than":        lambda key, value: key < value,
    "greater or equal": lambda key, value: key >= value,
    "less or equal":    lambda key, value: key <= value,
}

# The operators binary search can handle (it needs sorted, contiguous results)
BINARY_OPERATORS = {"equals", "greater than", "less than",
                    "greater or equal", "less or equal", "starts with"}


# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------
@dataclass
class Condition:
    column: str      # e.g. "year"
    operator: str    # e.g. "greater than"
    value: object    # whole number for numeric columns, lowercase text otherwise


def operators_for(column):
    """The operators that make sense for a column."""
    if column in Book.numeric_column_names():
        return NUMERIC_OPERATORS
    return TEXT_OPERATORS


def make_condition(column, operator, text):
    """Build a Condition from what the user typed.
    Raises ValueError with a readable message if the input is not valid."""
    text = text.strip()
    if not text:
        raise ValueError("Enter a value to search for.")
    if operator not in operators_for(column):
        raise ValueError(f"'{operator}' cannot be used on the '{column}' column.")

    if column in Book.numeric_column_names():
        try:
            value = int(text)
        except ValueError:
            raise ValueError(f"'{text}' is not a whole number.")
    else:
        value = text.lower()          # text is matched ignoring upper/lower case
    return Condition(column, operator, value)


# ---------------------------------------------------------------------------
# The algorithms. Each returns the list of matching books and counts its work
# in metrics.comparisons.
# ---------------------------------------------------------------------------
def linear_search(books, condition, metrics):
    """Check every book, one after another."""
    test = TESTS[condition.operator]
    matches = []
    for book in books:
        metrics.comparisons += 1                      # one test per book
        key = make_key(book.get(condition.column))
        if test(key, condition.value):
            matches.append(book)
    return matches


def binary_search(books, condition, metrics):
    """Find where the matches start and end in the SORTED list by halving
    the search range each step. The matches are always one block."""
    if condition.operator not in BINARY_OPERATORS:
        raise ValueError(f"Binary Search cannot do '{condition.operator}'. "
                         "Use Linear Search.")
    column, value, operator = condition.column, condition.value, condition.operator

    if operator == "equals":
        return books[_lower_bound(books, column, value, metrics):
                     _upper_bound(books, column, value, metrics)]
    if operator == "greater than":
        return books[_upper_bound(books, column, value, metrics):]
    if operator == "greater or equal":
        return books[_lower_bound(books, column, value, metrics):]
    if operator == "less than":
        return books[:_lower_bound(books, column, value, metrics)]
    if operator == "less or equal":
        return books[:_upper_bound(books, column, value, metrics)]

    # starts with: jump to the first key >= prefix, then walk forward while
    # the keys still start with the prefix
    position = _lower_bound(books, column, value, metrics)
    matches = []
    while position < len(books):
        metrics.comparisons += 1
        if not make_key(books[position].get(column)).startswith(value):
            break
        matches.append(books[position])
        position += 1
    return matches


def _lower_bound(books, column, value, metrics):
    """Index of the FIRST book whose key is >= value (halving the range)."""
    low, high = 0, len(books)
    while low < high:
        middle = (low + high) // 2
        metrics.comparisons += 1
        if make_key(books[middle].get(column)) < value:
            low = middle + 1          # the answer is to the right
        else:
            high = middle             # the answer is here or to the left
    return low


def _upper_bound(books, column, value, metrics):
    """Index of the FIRST book whose key is > value (halving the range)."""
    low, high = 0, len(books)
    while low < high:
        middle = (low + high) // 2
        metrics.comparisons += 1
        if make_key(books[middle].get(column)) <= value:
            low = middle + 1
        else:
            high = middle
    return low


# ---------------------------------------------------------------------------
# Registry and the function the rest of the app will call
# ---------------------------------------------------------------------------
@dataclass
class SearchAlgorithm:
    name: str
    function: object
    complexity: str
    needs_sorted: bool     # must the books be sorted by the searched column?
    operators: object = None   # operators it supports (None = all of them)


SEARCH_ALGORITHMS = {a.name: a for a in [
    SearchAlgorithm("Linear Search", linear_search, "O(n)",     needs_sorted=False),
    SearchAlgorithm("Binary Search", binary_search, "O(log n)", needs_sorted=True,
                    operators=BINARY_OPERATORS),
]}

def can_search(algorithm_name, operator):
    """Can this algorithm handle this operator?
    (Binary search cannot do 'contains' or 'ends with'.)"""
    allowed = SEARCH_ALGORITHMS[algorithm_name].operators
    return allowed is None or operator in allowed

@dataclass
class SearchResult:
    algorithm: str
    matches: list         # the matching books
    time_ms: float
    comparisons: int
    complexity: str


def _is_sorted_by(books, column):
    """True if the books are in ascending order of this column."""
    for i in range(1, len(books)):
        if make_key(books[i - 1].get(column)) > make_key(books[i].get(column)):
            return False
    return True


def run_search(algorithm_name, books, condition):
    """Search `books` for the condition with the named algorithm.
    The list is not changed. Returns a SearchResult."""
    algorithm = SEARCH_ALGORITHMS[algorithm_name]

    if algorithm.needs_sorted and not _is_sorted_by(books, condition.column):
        raise ValueError(f"{algorithm.name} needs the books sorted ascending "
                         f"by '{condition.column}'. Sort by that column first.")

    metrics = Metrics()
    start = time.perf_counter()
    matches = algorithm.function(books, condition, metrics)    # the actual search
    time_ms = (time.perf_counter() - start) * 1000

    return SearchResult(algorithm.name, matches, time_ms,
                        metrics.comparisons, algorithm.complexity)
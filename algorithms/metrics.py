"""Small data holders used by the sorting engine."""
from dataclasses import dataclass


class Metrics:
    """Counters that an algorithm updates while it runs."""

    def __init__(self):
        self.comparisons = 0   # times two keys were compared
        self.swaps = 0         # times an element was exchanged or moved


@dataclass
class SortResult:
    """Everything the UI will need to display after one sort."""
    algorithm: str        # e.g. "Bubble Sort"
    sorted_books: list    # the books, now in sorted order
    time_ms: float        # execution time in milliseconds
    comparisons: int
    swaps: int
    complexity: str       # e.g. "O(n^2)"
    stable: bool

    @property
    def stability(self):
        """Text version of 'stable' for display."""
        return "Stable" if self.stable else "Unstable"
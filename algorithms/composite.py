"""Composite search: several conditions combined with AND, OR and NOT.

Example:  year greater than 2000  AND  NOT genre equals fantasy

Rules:
  * NOT reverses one condition.
  * AND is applied before OR (as in normal logic):
        A OR B AND C   means   A OR (B AND C)

Every book is checked in turn (a linear scan). A book stops being checked as
soon as its result is known, e.g. when an AND condition fails.
comparisons = the number of single conditions tested.
"""
import time
from dataclasses import dataclass

from algorithms.metrics import Metrics
from algorithms.searching import TESTS, Condition, SearchResult, make_condition
from algorithms.sorting import make_key


@dataclass
class Term:
    condition: Condition
    negated: bool = False        # True = NOT


@dataclass
class CompositeFilter:
    terms: list                  # the Terms, left to right
    connectors: list             # "AND" / "OR" between neighbours (one fewer than terms)

    def groups(self):
        """Split into groups of ANDed terms. The groups are joined by OR,
        which is what 'AND before OR' means."""
        groups = [[self.terms[0]]]
        for connector, term in zip(self.connectors, self.terms[1:]):
            if connector == "AND":
                groups[-1].append(term)       # same group as the previous term
            else:
                groups.append([term])         # OR starts a new group
        return groups

    def describe(self):
        """The filter as readable text, e.g. 'year greater than 2000 AND NOT ...'."""
        parts = []
        for index, term in enumerate(self.terms):
            c = term.condition
            text = f"{'NOT ' if term.negated else ''}{c.column} {c.operator} {c.value}"
            if index > 0:
                text = f"{self.connectors[index - 1]} {text}"
            parts.append(text)
        return " ".join(parts)


def build_composite(rows):
    """Build a CompositeFilter from the rows of the dialog.
    Each row is (connector, negated, column, operator, text); the connector
    of the first row is ignored. Raises ValueError with a readable message."""
    if not rows:
        raise ValueError("Add at least one condition.")
    terms, connectors = [], []
    for index, (connector, negated, column, operator, text) in enumerate(rows):
        try:
            condition = make_condition(column, operator, text)
        except ValueError as error:
            raise ValueError(f"Condition {index + 1}: {error}")
        terms.append(Term(condition, negated))
        if index > 0:
            connectors.append(connector)
    return CompositeFilter(terms, connectors)


def composite_search(books, composite, metrics):
    """Return the books that satisfy the composite filter."""
    groups = composite.groups()
    matches = []
    for book in books:
        for group in groups:                       # OR: one matching group is enough
            if _group_matches(book, group, metrics):
                matches.append(book)
                break
    return matches


def _group_matches(book, group, metrics):
    """AND: every term in the group must match."""
    for term in group:
        metrics.comparisons += 1                   # one condition tested
        condition = term.condition
        key = make_key(book.get(condition.column))
        result = TESTS[condition.operator](key, condition.value)
        if term.negated:                           # NOT reverses the result
            result = not result
        if not result:
            return False                           # stop: this group cannot match
    return True


def run_composite_search(books, composite):
    """Run the composite filter on `books` (the list is not changed).
    Returns a SearchResult, like a normal search."""
    metrics = Metrics()
    start = time.perf_counter()
    matches = composite_search(books, composite, metrics)
    time_ms = (time.perf_counter() - start) * 1000
    return SearchResult("Composite Search", matches, time_ms,
                        metrics.comparisons, "O(n * m)")   # m = number of conditions
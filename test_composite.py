"""Test for composite search. Run:  python test_composite.py"""
import os

from algorithms.composite import build_composite, run_composite_search
from core.book import Book
from core.dataset import Dataset


def make_books(specs):
    """specs: (genre, year, language). Books are called 'Book 0', 'Book 1'..."""
    return [Book(f"Book {i}", "X", genre, "P", language, year, 100, 1)
            for i, (genre, year, language) in enumerate(specs)]


books = make_books([
    ("Fantasy", 1990, "eng"),    # Book 0
    ("Fantasy", 2005, "eng"),    # Book 1
    ("Fantasy", 2010, "fra"),    # Book 2
    ("Romance", 2001, "eng"),    # Book 3
    ("Romance", 1985, "eng"),    # Book 4
    ("Mystery", 2015, "spa"),    # Book 5
])


def titles(result):
    return [b.title.replace("Book ", "") for b in result.matches]


# ---------- Test 1: exact matches and comparisons on 6 books ----------
print("TEST 1: 6 books (Fantasy 1990, 2005, 2010 | Romance 2001, 1985 | Mystery 2015)")
cases = [
    # (description, rows, matching books, comparisons)
    ("single condition",
     [(None, False, "year", "greater than", "2000")],
     ["1", "2", "3", "5"], 6),
    ("AND",
     [(None, False, "year", "greater than", "2000"),
      ("AND", False, "genre", "equals", "Fantasy")],
     ["1", "2"], 10),
    ("OR",
     [(None, False, "genre", "equals", "romance"),
      ("OR", False, "year", "greater than", "2010")],
     ["3", "4", "5"], 10),
    ("NOT",
     [(None, True, "language", "equals", "eng")],
     ["2", "5"], 6),
    ("AND before OR",       # fantasy OR (romance AND year > 2000)
     [(None, False, "genre", "equals", "fantasy"),
      ("OR", False, "genre", "equals", "romance"),
      ("AND", False, "year", "greater than", "2000")],
     ["0", "1", "2", "3"], 11),
    ("AND with NOT",
     [(None, False, "genre", "equals", "fantasy"),
      ("AND", True, "year", "less than", "2000")],
     ["1", "2"], 9),
]
for label, rows, expected_titles, expected_comparisons in cases:
    result = run_composite_search(books, build_composite(rows))
    assert titles(result) == expected_titles, f"{label}: matches {titles(result)}"
    assert result.comparisons == expected_comparisons, f"{label}: {result.comparisons}"
    print(f"  {label:<16} {len(result.matches)} matches, "
          f"{result.comparisons:>2} comparisons  OK")

# ---------- Test 2: description text and errors ----------
print("\nTEST 2: description and invalid input")
composite = build_composite([(None, False, "year", "greater than", "2000"),
                             ("AND", True, "genre", "equals", "Fantasy")])
assert composite.describe() == "year greater than 2000 AND NOT genre equals fantasy"
print(f"  {composite.describe()}")

errors = {
    "no conditions": [],
    "empty value": [(None, False, "title", "contains", " ")],
    "text in a number column": [(None, False, "title", "contains", "a"),
                                ("AND", False, "year", "equals", "abc")],
}
for label, rows in errors.items():
    try:
        build_composite(rows)
        raise AssertionError(f"{label}: should have been refused")
    except ValueError as error:
        print(f"  {label}: {error}")

# ---------- Test 3: real data, checked against plain Python ----------
csv_path = os.path.join("data", "books.csv")
if not os.path.exists(csv_path):
    print("\ndata/books.csv not found - test 3 skipped")
else:
    dataset = Dataset()
    dataset.load_csv(csv_path)
    all_books = dataset.get_all()
    print(f"\nTEST 3: {len(all_books):,} real books")

    def check(label, rows, expected):
        result = run_composite_search(all_books, build_composite(rows))
        assert result.matches == expected, f"{label}: results differ"
        print(f"  {label:<44} {len(result.matches):>6,} matches "
              f"{result.comparisons:>7,} comparisons")
        return result

    check("year > 2000 AND genre = fantasy",
          [(None, False, "year", "greater than", "2000"),
           ("AND", False, "genre", "equals", "fantasy")],
          [b for b in all_books if b.year > 2000 and b.genre.lower() == "fantasy"])

    check("genre = fantasy OR NOT pages > 300",
          [(None, False, "genre", "equals", "fantasy"),
           ("OR", True, "pages", "greater than", "300")],
          [b for b in all_books if b.genre.lower() == "fantasy" or not b.pages > 300])

    plain = check("year > 2000",
                  [(None, False, "year", "greater than", "2000")],
                  [b for b in all_books if b.year > 2000])
    negated = check("NOT year > 2000",
                    [(None, True, "year", "greater than", "2000")],
                    [b for b in all_books if not b.year > 2000])
    assert len(plain.matches) + len(negated.matches) == len(all_books)

print("\nAll composite search checks passed.")
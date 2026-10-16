"""Data source: downloads books from the Open Library search API.

This file knows HOW to get books. It knows nothing about threads or the UI.
Only this file would change if we switched to a different website.
"""
import time

import requests

from core.book import Book

SEARCH_URL = "https://openlibrary.org/search.json"
# Open Library asks API users to identify their app. PUT YOUR EMAIL HERE.
USER_AGENT = "BookDataExplorer/1.0 (university DSA project; your_email@example.com)"

# The only fields we ask the API to send back
FIELDS = ("key,title,author_name,first_publish_year,publisher,language,"
          "number_of_pages_median,edition_count")

PAGE_SIZE = 100               # books requested per API call
MAX_PAGES_PER_SUBJECT = 30    # safety limit per subject
REQUEST_DELAY = 0.3           # seconds to wait between calls (be polite)
MAX_RETRIES = 3               # attempts per call before giving up

# We search subject by subject. The subject we searched for becomes the
# book's "genre", which gives one clean value per book.
SUBJECTS = [
    "Fiction", "Fantasy", "Science fiction", "Romance", "Mystery", "Thriller",
    "Horror", "History", "Biography", "Poetry", "Drama", "Philosophy",
    "Religion", "Science", "Mathematics", "Computers", "Medicine",
    "Psychology", "Economics", "Politics", "Art", "Music", "Travel",
    "Cooking", "Sports", "Education", "Law", "Nature", "Children",
    "Adventure", "Humor", "War",
]


class OpenLibrarySource:
    def iter_pages(self):
        """Generator: each time it is asked for the next item, it downloads
        one page of results and yields a list of complete Book objects."""
        seen_keys = set()      # a book can match several subjects; keep it once
        finished_subjects = set()

        # Go through the subjects in turns (page 1 of every subject, then
        # page 2 of every subject...) so genres stay evenly mixed.
        for page in range(1, MAX_PAGES_PER_SUBJECT + 1):
            for subject in SUBJECTS:
                if subject in finished_subjects:
                    continue

                docs = self._request(subject, page)
                if not docs:                     # no more results here
                    finished_subjects.add(subject)
                    continue

                books = []
                for doc in docs:
                    key = doc.get("key")
                    book = self._to_book(doc, subject)
                    if book is None or key in seen_keys:
                        continue                 # incomplete or duplicate
                    seen_keys.add(key)
                    books.append(book)

                yield books
                time.sleep(REQUEST_DELAY)

    def _request(self, subject, page):
        """Download one page of results. Retries a few times if the
        network fails. Returns the list of raw book dictionaries."""
        params = {
            "q": f'subject:"{subject}"',
            "fields": FIELDS,
            "limit": PAGE_SIZE,
            "page": page,
        }
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(SEARCH_URL, params=params,
                                        headers={"User-Agent": USER_AGENT},
                                        timeout=30)
                response.raise_for_status()      # error on HTTP 4xx / 5xx
                return response.json().get("docs", [])
            except (requests.RequestException, ValueError):
                if attempt == MAX_RETRIES - 1:   # last attempt failed
                    raise
                time.sleep(2)                    # wait, then try again

    @staticmethod
    def _to_book(doc, genre):
        """Convert one raw dictionary into a Book.
        Returns None if any of the 8 attributes is missing."""
        title = doc.get("title")
        authors = doc.get("author_name")
        publishers = doc.get("publisher")
        languages = doc.get("language")
        year = doc.get("first_publish_year")
        pages = doc.get("number_of_pages_median")
        editions = doc.get("edition_count")

        if not (title and authors and publishers and languages
                and year and pages and editions):
            return None

        return Book(
            title=title.strip(),
            author=authors[0],           # these fields are lists: take the first
            genre=genre,
            publisher=publishers[0],
            language=languages[0],
            year=int(year),
            pages=int(pages),
            editions=int(editions),
        )
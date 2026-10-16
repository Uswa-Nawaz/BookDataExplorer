import csv
import os
import sys
import threading
import time

import requests

API_URL = "https://openlibrary.org/search.json"
HEADERS = {"User-Agent": "BookDataExplorer (UET student project)"}
API_FIELDS = (
    "key,title,author_name,first_publish_year,number_of_pages_median,"
    "publisher,language,subject,edition_count,ratings_count,want_to_read_count"
)

COLUMNS = [
    "work_id", "title", "author", "first_publish_year", "pages",
    "edition_count", "ratings_count", "want_to_read_count",
    "publisher", "main_subject", "language_count",
]

# We mix subjects because one search can't give us 15k easily.
SUBJECTS = [
    "fiction", "history", "science", "romance", "fantasy", "mystery",
    "biography", "philosophy", "poetry", "horror", "art", "religion",
    "travel", "psychology", "business", "education",
]

PAGE_SIZE = 100
MAX_PAGES_PER_SUBJECT = 40

DEFAULT_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "books.csv"
)


def parse_doc(doc):
    """Turn one raw API record into a flat dict, or None if it's unusable."""
    title = doc.get("title")
    authors = doc.get("author_name")
    year = doc.get("first_publish_year")
    pages = doc.get("number_of_pages_median")
    key = doc.get("key")

    if not (title and authors and year and pages and key):
        return None

    publishers = doc.get("publisher") or []
    subjects = doc.get("subject") or []
    languages = doc.get("language") or []

    return {
        "work_id": key.replace("/works/", ""),
        "title": title.strip(),
        "author": authors[0].strip(),
        "first_publish_year": int(year),
        "pages": int(pages),
        "edition_count": int(doc.get("edition_count") or 0),
        "ratings_count": int(doc.get("ratings_count") or 0),
        "want_to_read_count": int(doc.get("want_to_read_count") or 0),
        "publisher": publishers[0].strip() if publishers else "Unknown",
        "main_subject": subjects[0].strip() if subjects else "Unknown",
        "language_count": len(languages),
    }


class OpenLibraryScraper:
    """Scrapes books on a background thread. Has NO UI code, so the UI
    only calls start / pause / resume / stop and listens to the callbacks."""

    def __init__(self, csv_path=DEFAULT_CSV, target=16000,
                 on_progress=None, on_finished=None):
        self.csv_path = csv_path
        self.target = target
        self.on_progress = on_progress    # called as on_progress(count, target)
        self.on_finished = on_finished    # called as on_finished(count, reason)

        self.count = 0
        self._seen = set()
        self._thread = None
        self._running = threading.Event()   # set = running, cleared = paused
        self._running.set()
        self._stop = threading.Event()

    # ---------- controls (the UI buttons call these) ----------
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._running.set()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self): 
        self._running.clear()

    def resume(self):
        self._running.set()

    def stop(self):
        self._stop.set()
        self._running.set()   # wake the thread if it was paused so it can exit

    # ---------- internals ----------
    def _load_existing(self):
        """If books.csv already exists, continue from it instead of starting over."""
        self._seen = set()
        if os.path.exists(self.csv_path):
            with open(self.csv_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    self._seen.add(row["work_id"])
        self.count = len(self._seen)

    def _fetch_page(self, subject, page):
        params = {
            "q": f"subject:{subject}",
            "limit": PAGE_SIZE,
            "page": page,
            "fields": API_FIELDS,
        }
        for attempt in range(3):
            try:
                r = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
                if r.status_code == 200:
                    return r.json().get("docs", [])
            except requests.RequestException:
                pass
            time.sleep(2 * (attempt + 1))   # wait longer after each failure
        return None

    def _run(self):
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        self._load_existing()
        is_new = not os.path.exists(self.csv_path)
        reason = "target reached"

        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            if is_new:
                writer.writeheader()

            for subject in SUBJECTS:
                for page in range(1, MAX_PAGES_PER_SUBJECT + 1):
                    self._running.wait()            # blocks here while paused
                    if self._stop.is_set():
                        reason = "stopped"
                        break
                    if self.count >= self.target:
                        break

                    docs = self._fetch_page(subject, page)
                    if docs is None:
                        continue                    # page failed 3 times, skip it
                    if not docs:
                        break                       # subject ran out of results

                    for doc in docs:
                        book = parse_doc(doc)
                        if book and book["work_id"] not in self._seen:
                            self._seen.add(book["work_id"])
                            writer.writerow(book)
                            self.count += 1
                            if self.count >= self.target:
                                break
                    f.flush()

                    if self.on_progress:
                        self.on_progress(self.count, self.target)
                    time.sleep(0.3)                 # be polite to the server

                if self._stop.is_set() or self.count >= self.target:
                    break
            else:
                reason = "ran out of subjects"

        if self.on_finished:
            self.on_finished(self.count, reason)


# Quick console test:  python scraper/open_library.py 300
if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 300

    def show(count, total):
        print(f"\rScraped {count}/{total}", end="", flush=True)

    def done(count, reason):
        print(f"\nFinished: {count} books ({reason})")

    scraper = OpenLibraryScraper(target=target, on_progress=show, on_finished=done)
    scraper.start()
    scraper._thread.join()
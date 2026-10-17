"""Main window: holds the tabs and connects the tabs to the data."""
import os

from PyQt5.QtWidgets import QMainWindow, QTabWidget

from core.dataset import Dataset
from scraper.open_library_source import OpenLibrarySource
from scraper.scraper_thread import ScraperThread
from ui.books_tab import BooksTab
from ui.scraper_tab import IDLE, ScraperTab

TARGET_BOOKS = 15000

# Absolute path to  book_data_explorer/data/books.csv
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "books.csv")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Book Data Explorer")
        self.resize(1100, 780)

        self.dataset = Dataset()     # all books are stored here
        self._thread = None          # the current scraper thread (if any)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.books_tab = BooksTab()
        self.tabs.addTab(self.books_tab, "Books")

        self.scraper_tab = ScraperTab(target_count=TARGET_BOOKS)
        self.tabs.addTab(self.scraper_tab, "Scraper")

        # Connect the tab's button signals to our handlers
        self.scraper_tab.start_requested.connect(self._start_scraping)
        self.scraper_tab.pause_requested.connect(self._pause_scraping)
        self.scraper_tab.resume_requested.connect(self._resume_scraping)
        self.scraper_tab.stop_requested.connect(self._stop_scraping)

        self._load_saved_books()

    # ---------- loading saved data ----------
    def _load_saved_books(self):
        """At startup, load the CSV from the last scrape (if it exists)."""
        if os.path.exists(CSV_PATH):
            self.dataset.load_csv(CSV_PATH)
            self.books_tab.show_books(self.dataset.get_all())

    # ---------- scraper control ----------
    def _start_scraping(self):
        # If a previous run is still shutting down, wait for it to end
        if self._thread is not None and self._thread.isRunning():
            self._thread.wait()

        self.dataset.clear()
        self.scraper_tab.set_progress(0)

        self._thread = ScraperThread(self.dataset, OpenLibrarySource(),
                                     TARGET_BOOKS)
        self._thread.progress.connect(self.scraper_tab.set_progress)
        self._thread.scraping_finished.connect(self._on_scraping_finished)
        self._thread.start()

    def _pause_scraping(self):
        self._thread.pause()

    def _resume_scraping(self):
        self._thread.resume()

    def _stop_scraping(self):
        self._thread.stop()

    def _on_scraping_finished(self, message):
        # Ignore a late message from an OLD thread (after a quick Stop -> Start)
        if self.sender() is not self._thread:
            return

        self.scraper_tab.set_state(IDLE)
        count = len(self.dataset)
        if count > 0:
            self.dataset.save_csv(CSV_PATH)    # keep whatever was scraped
            self.books_tab.show_books(self.dataset.get_all())   # refresh table
            message += f". {count} books saved to data/books.csv"
        self.scraper_tab.show_message(message)

    def closeEvent(self, event):
        """Stop the thread cleanly when the window is closed."""
        if self._thread is not None and self._thread.isRunning():
            self._thread.stop()
            self._thread.wait()
        self.books_tab.finish_sort()
        event.accept()
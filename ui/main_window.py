"""Main window: holds the tabs. More tabs are added in later phases."""
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QTabWidget

from ui.scraper_tab import IDLE, ScraperTab

TARGET_BOOKS = 15000


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Book Data Explorer")
        self.resize(900, 600)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.scraper_tab = ScraperTab(target_count=TARGET_BOOKS)
        self.tabs.addTab(self.scraper_tab, "Scraper")

        self._setup_demo()   # TEMPORARY: delete in the scraper step

    # ------------------------------------------------------------------
    # TEMPORARY DEMO CODE: a fake "scraper" that only counts upward so we
    # can see the buttons and progress bar working. It will be replaced
    # by the real scraper later.
    # ------------------------------------------------------------------
    def _setup_demo(self):
        self._demo_count = 0
        self._demo_timer = QTimer(self)
        self._demo_timer.setInterval(20)                  # tick every 20 ms
        self._demo_timer.timeout.connect(self._demo_tick)

        self.scraper_tab.start_requested.connect(self._demo_start)
        self.scraper_tab.pause_requested.connect(self._demo_timer.stop)
        self.scraper_tab.resume_requested.connect(self._demo_timer.start)
        self.scraper_tab.stop_requested.connect(self._demo_timer.stop)

    def _demo_start(self):
        self._demo_count = 0
        self.scraper_tab.set_progress(0)
        self._demo_timer.start()

    def _demo_tick(self):
        self._demo_count += 50                            # "scrape" 50 books
        self.scraper_tab.set_progress(self._demo_count)
        if self._demo_count >= TARGET_BOOKS:              # finished
            self._demo_timer.stop()
            self.scraper_tab.set_state(IDLE)
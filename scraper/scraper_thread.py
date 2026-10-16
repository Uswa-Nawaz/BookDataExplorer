"""Background thread that runs the scraper without freezing the UI."""
from PyQt5.QtCore import QThread, pyqtSignal


class ScraperThread(QThread):
    progress = pyqtSignal(int)             # sent with the current book count
    scraping_finished = pyqtSignal(str)    # sent once, with the reason

    def __init__(self, dataset, source, target_count):
        super().__init__()
        self._dataset = dataset
        self._source = source
        self._target_count = target_count
        self._paused = False               # flags set by the UI buttons
        self._stopped = False

    # ---------- called from the UI thread ----------
    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def stop(self):
        self._stopped = True

    # ---------- runs in the background thread ----------
    def run(self):
        """QThread calls this automatically after start()."""
        try:
            message = self._scrape()
        except Exception as error:         # e.g. no internet connection
            message = f"Error: {error}"
        self.scraping_finished.emit(message)

    def _scrape(self):
        for books in self._source.iter_pages():
            # Pause: wait here (checking every 100 ms) until resumed or stopped
            while self._paused and not self._stopped:
                self.msleep(100)
            if self._stopped:
                return "Stopped by user"

            # Add the new books, but never go past the target
            for book in books:
                self._dataset.add(book)
                if len(self._dataset) >= self._target_count:
                    break
            self.progress.emit(len(self._dataset))

            if len(self._dataset) >= self._target_count:
                return "Target reached"
        return "No more books available from the source"
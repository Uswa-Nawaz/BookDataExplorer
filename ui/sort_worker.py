"""Runs one sort in a separate PROCESS so the window stays responsive.

Why a process and not just a thread? Python lets only one thread run Python
code at a time (the "GIL"). A sort running in a thread competes with the
window for that lock, which freezes the window. A separate process has its
own lock, so the window is not affected. It also gives cleaner timings.
"""
from concurrent.futures import ProcessPoolExecutor

from PyQt5.QtCore import QThread, pyqtSignal


class SortThread(QThread):
    sort_finished = pyqtSignal(object)   # carries the SortResult
    sort_failed = pyqtSignal(str)        # carries an error message

    def __init__(self, sort_function, *arguments, descending=False):
        """sort_function is run_sort or run_multi_sort; arguments are passed to it."""
        super().__init__()
        self._sort_function = sort_function
        self._arguments = arguments
        self._descending = descending

    def run(self):
        """QThread calls this automatically after start()."""
        try:
            # Start one helper process, run the sort there, and wait for the
            # result. While waiting, this thread uses no CPU.
            with ProcessPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._sort_function, *self._arguments)
                result = future.result()
            if self._descending:
                # Descending = the ascending result reversed. The measured
                # time and counts are those of the ascending sort itself.
                result.sorted_books.reverse()
            self.sort_finished.emit(result)
        except Exception as error:
            self.sort_failed.emit(str(error))
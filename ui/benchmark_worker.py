"""Runs the benchmark: every applicable algorithm on one column.

Like a single sort, each algorithm runs in a helper PROCESS so the window
stays responsive. The same helper process is used for all of them, one after
another, so every algorithm gets the same input and the same conditions.
"""
from concurrent.futures import ProcessPoolExecutor

from PyQt5.QtCore import QThread, pyqtSignal

from algorithms.sorting import ALGORITHMS, is_available, run_sort


class BenchmarkThread(QThread):
    progress = pyqtSignal(int, int, str)     # position, total, algorithm name
    benchmark_finished = pyqtSignal(list)    # list of SortResult (metrics only)
    benchmark_failed = pyqtSignal(str)

    def __init__(self, books, column):
        super().__init__()
        self._books = books
        self._column = column
        self._stopped = False

    def stop(self):
        """Stop after the algorithm that is currently running."""
        self._stopped = True

    def run(self):
        try:
            # Numeric-only algorithms are skipped for text columns
            names = [name for name in ALGORITHMS
                     if is_available(name, self._column)]
            results = []
            with ProcessPoolExecutor(max_workers=1) as executor:
                for position, name in enumerate(names, start=1):
                    if self._stopped:
                        return
                    self.progress.emit(position, len(names), name)
                    future = executor.submit(run_sort, name, self._books,
                                             self._column)
                    result = future.result()
                    result.sorted_books = []     # the table only needs the metrics
                    results.append(result)
            self.benchmark_finished.emit(results)
        except Exception as error:
            self.benchmark_failed.emit(str(error))
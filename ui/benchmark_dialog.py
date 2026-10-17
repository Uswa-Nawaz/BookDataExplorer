"""Pop-up window that shows the benchmark results as a comparison table."""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QAbstractItemView, QDialog, QHeaderView, QLabel,
                             QTableWidget, QTableWidgetItem, QVBoxLayout)

from algorithms.sorting import ALGORITHMS

HEADERS = ["Algorithm", "Time (ms)", "Comparisons", "Swaps",
           "Complexity", "Stability"]
NUMBER_COLUMNS = (1, 2, 3)      # these columns are right-aligned


class BenchmarkDialog(QDialog):
    def __init__(self, column, book_count, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Benchmark - {column.capitalize()}")
        self.resize(780, 440)

        results_by_name = {result.algorithm: result for result in results}
        fastest = min(results, key=lambda r: r.time_ms).algorithm

        heading = QLabel(f"All algorithms on {book_count:,} books, "
                         f"sorted by {column.capitalize()}")
        heading.setStyleSheet("font-size: 15px; font-weight: bold;")
        note = QLabel("Green = fastest.  N/A = needs a numeric column.  "
                      "Times change with machine load; "
                      "comparisons and swaps do not.")
        note.setStyleSheet("color: gray;")

        # One row per algorithm in the registry (N/A if it was skipped)
        table = QTableWidget(len(ALGORITHMS), len(HEADERS))
        table.setHorizontalHeaderLabels(HEADERS)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        for row, (name, algorithm) in enumerate(ALGORITHMS.items()):
            result = results_by_name.get(name)
            if result is None:           # skipped for this column
                values = [name, "N/A", "N/A", "N/A", algorithm.complexity,
                          "Stable" if algorithm.stable else "Unstable"]
            else:
                values = [name, f"{result.time_ms:,.2f}",
                          f"{result.comparisons:,}", f"{result.swaps:,}",
                          result.complexity, result.stability]

            for column_index, text in enumerate(values):
                item = QTableWidgetItem(text)
                if column_index in NUMBER_COLUMNS:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if result is None:
                    item.setForeground(QColor("gray"))
                elif name == fastest:
                    item.setBackground(QColor("#d4f4dd"))
                    item.setForeground(QColor("black"))
                table.setItem(row, column_index, item)

        layout = QVBoxLayout()
        layout.addWidget(heading)
        layout.addWidget(table)
        layout.addWidget(note)
        self.setLayout(layout)
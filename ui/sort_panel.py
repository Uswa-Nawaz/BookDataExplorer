"""Sorting controls (column, algorithm, order) and the results display."""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QComboBox, QGridLayout, QGroupBox, QHBoxLayout,
                             QLabel, QPushButton, QVBoxLayout)

from algorithms.sorting import ALGORITHMS
from core.book import Book

RESULT_FIELDS = ["Algorithm", "Time", "Comparisons", "Swaps",
                 "Complexity", "Stability"]


class SortPanel(QGroupBox):
    # Sent when a button is clicked; the Books tab decides what to do.
    sort_requested = pyqtSignal(str, str, bool)   # algorithm, column, descending
    reset_requested = pyqtSignal()

    def __init__(self):
        super().__init__("Sorting")
        self._build_ui()

    def _build_ui(self):
        # --- controls ---
        self.column_box = QComboBox()
        for name in Book.column_names():
            self.column_box.addItem(name.capitalize(), name)   # (shown text, value)

        self.algorithm_box = QComboBox()
        self.algorithm_box.addItems(list(ALGORITHMS))          # names from the registry

        self.order_box = QComboBox()
        self.order_box.addItems(["Ascending", "Descending"])

        self.sort_button = QPushButton("Sort")
        self.reset_button = QPushButton("Reset order")
        self.sort_button.clicked.connect(self._on_sort_clicked)
        self.reset_button.clicked.connect(self.reset_requested.emit)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Column:"))
        controls.addWidget(self.column_box)
        controls.addWidget(QLabel("Algorithm:"))
        controls.addWidget(self.algorithm_box)
        controls.addWidget(QLabel("Order:"))
        controls.addWidget(self.order_box)
        controls.addWidget(self.sort_button)
        controls.addWidget(self.reset_button)
        controls.addStretch()

        # --- results: a caption row above a value row ---
        results = QGridLayout()
        self._value_labels = {}
        for position, field in enumerate(RESULT_FIELDS):
            caption = QLabel(field)
            caption.setStyleSheet("color: gray;")
            value = QLabel("-")
            value.setStyleSheet("font-weight: bold;")
            results.addWidget(caption, 0, position)
            results.addWidget(value, 1, position)
            self._value_labels[field] = value

        self.status_label = QLabel("")

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addLayout(results)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

    # ---------- button handler ----------
    def _on_sort_clicked(self):
        self.sort_requested.emit(
            self.algorithm_box.currentText(),
            self.column_box.currentData(),             # e.g. "year"
            self.order_box.currentText() == "Descending")

    # ---------- called by the Books tab ----------
    def set_busy(self, busy):
        """Disable the controls while a sort is running."""
        for widget in (self.column_box, self.algorithm_box, self.order_box,
                       self.sort_button, self.reset_button):
            widget.setEnabled(not busy)
        self.show_status("Sorting... please wait" if busy else "")

    def show_status(self, text):
        self.status_label.setText(text)

    def show_result(self, result):
        """Fill in the six result values from a SortResult."""
        values = {
            "Algorithm": result.algorithm,
            "Time": f"{result.time_ms:,.2f} ms",
            "Comparisons": f"{result.comparisons:,}",
            "Swaps": f"{result.swaps:,}",
            "Complexity": result.complexity,
            "Stability": result.stability,
        }
        for field, text in values.items():
            self._value_labels[field].setText(text)

    def clear_result(self):
        for label in self._value_labels.values():
            label.setText("-")
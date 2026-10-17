"""Search controls (column, filter, value, algorithm) and the results display."""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QComboBox, QGridLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QVBoxLayout)

from algorithms.searching import SEARCH_ALGORITHMS, can_search, operators_for
from core.book import Book

RESULT_FIELDS = ["Algorithm", "Time", "Comparisons", "Matches", "Complexity"]


class SearchPanel(QGroupBox):
    # Sent when a button is clicked; the Books tab decides what to do.
    search_requested = pyqtSignal(str, str, str, str)   # algorithm, column, operator, text
    clear_requested = pyqtSignal()

    def __init__(self):
        super().__init__("Search")
        self._build_ui()

    def _build_ui(self):
        # --- controls ---
        self.column_box = QComboBox()
        for name in Book.column_names():
            self.column_box.addItem(name.capitalize(), name)   # (shown text, value)

        self.operator_box = QComboBox()          # filled by _update_operators
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Value to search for")

        self.algorithm_box = QComboBox()
        self.algorithm_box.addItems(list(SEARCH_ALGORITHMS))

        self.search_button = QPushButton("Search")
        self.clear_button = QPushButton("Clear search")

        # The list of filters depends on the column, and the usable
        # algorithms depend on the filter
        self.column_box.currentIndexChanged.connect(self._update_operators)
        self.operator_box.currentIndexChanged.connect(self._update_available_algorithms)
        self.search_button.clicked.connect(self._on_search_clicked)
        self.value_edit.returnPressed.connect(self._on_search_clicked)   # Enter key
        self.clear_button.clicked.connect(self.clear_requested.emit)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Column:"))
        controls.addWidget(self.column_box)
        controls.addWidget(QLabel("Filter:"))
        controls.addWidget(self.operator_box)
        controls.addWidget(self.value_edit, 1)       # takes the spare width
        controls.addWidget(QLabel("Algorithm:"))
        controls.addWidget(self.algorithm_box)
        controls.addWidget(self.search_button)
        controls.addWidget(self.clear_button)

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

        self._update_operators()          # fill the filter list for the first column

    # ---------- keeping the dropdowns consistent ----------
    def _update_operators(self):
        """Show only the filters that make sense for the selected column."""
        column = self.column_box.currentData()
        self.operator_box.blockSignals(True)     # don't react while refilling
        self.operator_box.clear()
        self.operator_box.addItems(operators_for(column))
        self.operator_box.blockSignals(False)
        self._update_available_algorithms()

    def _update_available_algorithms(self):
        """Grey out algorithms that cannot do the selected filter."""
        operator = self.operator_box.currentText()
        model = self.algorithm_box.model()
        for index, name in enumerate(SEARCH_ALGORITHMS):
            model.item(index).setEnabled(can_search(name, operator))
        if not can_search(self.algorithm_box.currentText(), operator):
            self.algorithm_box.setCurrentIndex(0)

    # ---------- button handler ----------
    def _on_search_clicked(self):
        self.search_requested.emit(
            self.algorithm_box.currentText(),
            self.column_box.currentData(),             # e.g. "title"
            self.operator_box.currentText(),           # e.g. "contains"
            self.value_edit.text())

    # ---------- called by the Books tab ----------
    def show_status(self, text):
        self.status_label.setText(text)

    def show_result(self, result, total):
        """Fill in the results from a SearchResult; total = books searched."""
        values = {
            "Algorithm": result.algorithm,
            "Time": f"{result.time_ms:,.3f} ms",
            "Comparisons": f"{result.comparisons:,}",
            "Matches": f"{len(result.matches):,} of {total:,}",
            "Complexity": result.complexity,
        }
        for field, text in values.items():
            self._value_labels[field].setText(text)
        self.show_status("")

    def clear_result(self):
        for label in self._value_labels.values():
            label.setText("-")
        self.show_status("")
"""Pop-up window for choosing several columns to sort by."""
from PyQt5.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QLabel,
                             QPushButton, QVBoxLayout, QWidget)

from algorithms.sorting import ALGORITHMS
from core.book import Book


class LevelRow(QWidget):
    """One sort level:  Sort by / Then by   column   Ascending / Descending   [x]"""

    def __init__(self, remove_callback):
        super().__init__()
        self.position_label = QLabel()
        self.position_label.setFixedWidth(60)

        self.column_box = QComboBox()
        for name in Book.column_names():
            self.column_box.addItem(name.capitalize(), name)
        self.order_box = QComboBox()
        self.order_box.addItems(["Ascending", "Descending"])

        self.remove_button = QPushButton("x")
        self.remove_button.setFixedWidth(30)
        self.remove_button.clicked.connect(lambda: remove_callback(self))

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.position_label)
        layout.addWidget(self.column_box)
        layout.addWidget(self.order_box)
        layout.addWidget(self.remove_button)
        layout.addStretch()
        self.setLayout(layout)

    def set_position(self, index):
        self.position_label.setText("Sort by" if index == 0 else "Then by")

    def value(self):
        """(column, descending) for this level."""
        return (self.column_box.currentData(),
                self.order_box.currentText() == "Descending")


class MultiSortDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Multi-level sort")
        self.resize(520, 320)
        self.algorithm_name = None    # set when the user clicks Apply
        self.levels = None            # [(column, descending), ...]
        self._rows = []

        hint = QLabel("Books are sorted by the first column. Books that are equal "
                      "in it are then sorted by the next column, and so on.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray;")

        # Counting, radix and bucket sort cannot sort by several columns
        self.algorithm_box = QComboBox()
        self.algorithm_box.addItems(
            [name for name, algorithm in ALGORITHMS.items()
             if not algorithm.numeric_only])
        algorithm_row = QHBoxLayout()
        algorithm_row.addWidget(QLabel("Algorithm:"))
        algorithm_row.addWidget(self.algorithm_box)
        algorithm_row.addStretch()

        self._rows_layout = QVBoxLayout()
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #c0392b;")

        add_button = QPushButton("+ Add level")
        apply_button = QPushButton("Sort")
        apply_button.setDefault(True)
        cancel_button = QPushButton("Cancel")
        add_button.clicked.connect(self._add_row)
        apply_button.clicked.connect(self._on_apply)
        cancel_button.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addStretch()
        buttons.addWidget(cancel_button)
        buttons.addWidget(apply_button)

        layout = QVBoxLayout()
        layout.addWidget(hint)
        layout.addLayout(algorithm_row)
        layout.addLayout(self._rows_layout)
        layout.addWidget(self.error_label)
        layout.addStretch()
        layout.addLayout(buttons)
        self.setLayout(layout)

        self._add_row()               # start with two levels
        self._add_row()

    def _add_row(self):
        row = LevelRow(self._remove_row)
        # Suggest the first column that is not used yet
        used = [existing.value()[0] for existing in self._rows]
        for index in range(row.column_box.count()):
            if row.column_box.itemData(index) not in used:
                row.column_box.setCurrentIndex(index)
                break
        self._rows.append(row)
        self._rows_layout.addWidget(row)
        self._update_positions()

    def _remove_row(self, row):
        if len(self._rows) == 1:      # always keep at least one level
            return
        self._rows.remove(row)
        self._rows_layout.removeWidget(row)
        row.deleteLater()
        self._update_positions()

    def _update_positions(self):
        for index, row in enumerate(self._rows):
            row.set_position(index)

    def _on_apply(self):
        """Check the levels; if they are invalid, show why and stay open."""
        levels = [row.value() for row in self._rows]
        columns = [column for column, _ in levels]
        if len(set(columns)) != len(columns):
            self.error_label.setText("Each column can be used only once.")
            return
        self.error_label.setText("")
        self.levels = levels
        self.algorithm_name = self.algorithm_box.currentText()
        self.accept()
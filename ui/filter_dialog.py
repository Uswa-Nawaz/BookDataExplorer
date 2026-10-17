"""Pop-up window for building a composite filter (AND / OR / NOT)."""
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QVBoxLayout, QWidget)

from algorithms.composite import build_composite
from algorithms.searching import operators_for
from core.book import Book


class ConditionRow(QWidget):
    """One line of the dialog:  [AND/OR] [NOT] column  filter  value  [x]"""

    def __init__(self, remove_callback):
        super().__init__()
        self.where_label = QLabel("Where")           # shown on the first row only
        self.where_label.setFixedWidth(70)
        self.connector_box = QComboBox()             # shown on the other rows
        self.connector_box.addItems(["AND", "OR"])
        self.connector_box.setFixedWidth(70)

        self.not_check = QCheckBox("NOT")
        self.column_box = QComboBox()
        for name in Book.column_names():
            self.column_box.addItem(name.capitalize(), name)
        self.operator_box = QComboBox()
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Value")
        self.remove_button = QPushButton("x")
        self.remove_button.setFixedWidth(30)

        self.column_box.currentIndexChanged.connect(self._update_operators)
        self.remove_button.clicked.connect(lambda: remove_callback(self))

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.where_label)
        layout.addWidget(self.connector_box)
        layout.addWidget(self.not_check)
        layout.addWidget(self.column_box)
        layout.addWidget(self.operator_box)
        layout.addWidget(self.value_edit, 1)         # takes the spare width
        layout.addWidget(self.remove_button)
        self.setLayout(layout)

        self._update_operators()

    def _update_operators(self):
        """Show only the filters that make sense for the selected column."""
        self.operator_box.clear()
        self.operator_box.addItems(operators_for(self.column_box.currentData()))

    def set_first(self, is_first):
        """The first row has no AND/OR in front of it."""
        self.where_label.setVisible(is_first)
        self.connector_box.setVisible(not is_first)

    def values(self):
        """(connector, negated, column, operator, text) for build_composite."""
        return (self.connector_box.currentText(), self.not_check.isChecked(),
                self.column_box.currentData(), self.operator_box.currentText(),
                self.value_edit.text())


class FilterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Composite filter")
        self.resize(820, 300)
        self.composite = None        # the filter built when the user clicks Apply
        self._rows = []

        hint = QLabel("Combine conditions with AND / OR. NOT reverses a condition. "
                      "AND is applied before OR.")
        hint.setStyleSheet("color: gray;")

        self._rows_layout = QVBoxLayout()
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #c0392b;")

        add_button = QPushButton("+ Add condition")
        apply_button = QPushButton("Apply filter")
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
        layout.addLayout(self._rows_layout)
        layout.addWidget(self.error_label)
        layout.addStretch()
        layout.addLayout(buttons)
        self.setLayout(layout)

        self._add_row()              # start with one condition

    def _add_row(self):
        row = ConditionRow(self._remove_row)
        self._rows.append(row)
        self._rows_layout.addWidget(row)
        self._update_first_flags()

    def _remove_row(self, row):
        if len(self._rows) == 1:     # always keep at least one condition
            return
        self._rows.remove(row)
        self._rows_layout.removeWidget(row)
        row.deleteLater()
        self._update_first_flags()

    def _update_first_flags(self):
        for index, row in enumerate(self._rows):
            row.set_first(index == 0)

    def _on_apply(self):
        """Build the filter; if the input is invalid, show why and stay open."""
        try:
            self.composite = build_composite([row.values() for row in self._rows])
        except ValueError as error:
            self.error_label.setText(str(error))
            return
        self.error_label.setText("")
        self.accept()
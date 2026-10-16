from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from algorithms.searching import SEARCH_ALGORITHMS
from core.data_manager import COLUMNS, DataManager
from core.filters import NUM_OPS, TEXT_OPS


def pretty(col):
    return col.replace("_", " ").title()


class SearchPanel(QWidget):
    search_requested = pyqtSignal(str, str, str)   # column, algorithm, text
    cleared = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.col_combo = QComboBox()
        for c in COLUMNS:
            self.col_combo.addItem(pretty(c), c)
        self.col_combo.currentIndexChanged.connect(self._update_algorithms)

        self.algo_combo = QComboBox()
        self.algo_combo.setMinimumWidth(380)
        for name, info in SEARCH_ALGORITHMS.items():
            label = f"{name}  |  {info['complexity']}"
            if info["needs_sorted"]:
                label += "  |  uses sorted index"
            if info["numeric_only"]:
                label += "  |  numeric columns only"
            self.algo_combo.addItem(label, name)

        self.text = QLineEdit()
        self.text.setPlaceholderText("exact value, e.g. 2018 or Jenny Han")
        self.text.returnPressed.connect(self._emit)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._emit)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.cleared.emit)

        row = QHBoxLayout()
        for label, w in [("Column:", self.col_combo), ("Algorithm:", self.algo_combo)]:
            row.addWidget(QLabel(label))
            row.addWidget(w)
        row.addWidget(QLabel("Value:"))
        row.addWidget(self.text, 1)
        row.addWidget(search_btn)
        row.addWidget(clear_btn)

        self.result = QLabel("")
        note = QLabel("Exact match (case-insensitive). For contains / starts with / ends with, "
                      "use the Advanced Filters tab.")

        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self.result)
        layout.addWidget(note)
        layout.addStretch()
        self._update_algorithms()

    def _update_algorithms(self):
        numeric = DataManager.is_numeric(self.col_combo.currentData())
        model = self.algo_combo.model()
        for i in range(self.algo_combo.count()):
            name = self.algo_combo.itemData(i)
            model.item(i).setEnabled(numeric or not SEARCH_ALGORITHMS[name]["numeric_only"])
        if not model.item(self.algo_combo.currentIndex()).isEnabled():
            self.algo_combo.setCurrentIndex(0)

    def _emit(self):
        text = self.text.text().strip()
        if not text:
            self.set_result("Type a value to search for.")
            return
        self.search_requested.emit(self.col_combo.currentData(),
                                   self.algo_combo.currentData(), text)

    def set_result(self, text):
        self.result.setText(text)


class ConditionRow(QWidget):
    removed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.where = QLabel("Where")
        self.where.setFixedWidth(60)
        self.connector = QComboBox()
        self.connector.addItems(["AND", "OR"])
        self.connector.setFixedWidth(60)

        self.not_box = QCheckBox("NOT")
        self.col = QComboBox()
        for c in COLUMNS:
            self.col.addItem(pretty(c), c)
        self.op = QComboBox()
        self.value = QLineEdit()
        self.value.setPlaceholderText("value")
        remove = QPushButton("✕")
        remove.setFixedWidth(30)
        remove.clicked.connect(lambda: self.removed.emit(self))

        self.col.currentIndexChanged.connect(self._update_ops)
        self._update_ops()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for w in (self.where, self.connector, self.not_box, self.col, self.op):
            layout.addWidget(w)
        layout.addWidget(self.value, 1)
        layout.addWidget(remove)

    def _update_ops(self):
        numeric = DataManager.is_numeric(self.col.currentData())
        self.op.clear()
        self.op.addItems(NUM_OPS if numeric else TEXT_OPS)

    def set_first(self, first):
        self.where.setVisible(first)
        self.connector.setVisible(not first)

    def to_dict(self):
        return {
            "connector": self.connector.currentText(),
            "negate": self.not_box.isChecked(),
            "column": self.col.currentData(),
            "op": self.op.currentText(),
            "value": self.value.text(),
        }


class FilterPanel(QWidget):
    apply_requested = pyqtSignal(list)
    cleared = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.rows = []

        self.rows_layout = QVBoxLayout()
        self.rows_layout.addStretch()
        holder = QWidget()
        holder.setLayout(self.rows_layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(holder)

        add_btn = QPushButton("+ Add condition")
        add_btn.clicked.connect(self.add_row)
        apply_btn = QPushButton("Apply filters")
        apply_btn.clicked.connect(self._apply)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear)

        buttons = QHBoxLayout()
        buttons.addWidget(add_btn)
        buttons.addWidget(apply_btn)
        buttons.addWidget(clear_btn)
        buttons.addStretch()

        self.result = QLabel("")
        note = QLabel("Conditions run top to bottom. AND is applied before OR. "
                      "NOT flips a single condition.")

        layout = QVBoxLayout(self)
        layout.addWidget(scroll, 1)
        layout.addLayout(buttons)
        layout.addWidget(self.result)
        layout.addWidget(note)
        self.add_row()

    def add_row(self):
        row = ConditionRow()
        row.removed.connect(self.remove_row)
        self.rows.append(row)
        self.rows_layout.insertWidget(len(self.rows) - 1, row)
        self._renumber()

    def remove_row(self, row):
        if len(self.rows) == 1:
            row.value.clear()
            return
        self.rows.remove(row)
        self.rows_layout.removeWidget(row)
        row.deleteLater()
        self._renumber()

    def _renumber(self):
        for i, r in enumerate(self.rows):
            r.set_first(i == 0)

    def _apply(self):
        conds = [r.to_dict() for r in self.rows if r.value.text().strip()]
        if not conds:
            self.set_result("Enter a value in at least one condition.")
            return
        self.apply_requested.emit(conds)

    def _clear(self):
        for r in self.rows[1:]:
            self.rows_layout.removeWidget(r)
            r.deleteLater()
        self.rows = self.rows[:1]
        self.rows[0].value.clear()
        self.rows[0].not_box.setChecked(False)
        self._renumber()
        self.cleared.emit()

    def set_result(self, text):
        self.result.setText(text)
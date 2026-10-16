from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QTableView, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget,
)

from algorithms.searching import run_search
from algorithms.sorting import ALGORITHMS, run_sort
from core.data_manager import COLUMNS, DataManager
from core.filters import apply_filters
from ui.query_panels import FilterPanel, SearchPanel

def make_key(column):
    """Numbers sort as numbers, text sorts case-insensitively."""
    if DataManager.is_numeric(column):
        return lambda r: r[column]
    return lambda r: r[column].lower()


# ---------------- background workers (keep the UI from freezing) ----------------

class SortWorker(QThread):
    done = pyqtSignal(list, dict)

    def __init__(self, rows, key, algorithm, reverse):
        super().__init__()
        self.rows, self.key, self.algorithm, self.reverse = rows, key, algorithm, reverse

    def run(self):
        out, metrics = run_sort(self.rows, self.key, self.algorithm, self.reverse)
        self.done.emit(out, metrics)


class BenchmarkWorker(QThread):
    progress = pyqtSignal(str)
    done = pyqtSignal(list)

    def __init__(self, rows, key, numeric, reverse):
        super().__init__()
        self.rows, self.key, self.numeric, self.reverse = rows, key, numeric, reverse

    def run(self):
        results = []
        for name, info in ALGORITHMS.items():
            if info["numeric_only"] and not self.numeric:
                results.append((name, None))
                continue
            self.progress.emit(name)
            _, metrics = run_sort(self.rows, self.key, name, self.reverse)
            results.append((name, metrics))
        self.done.emit(results)


# ---------------- table model ----------------

class BookTableModel(QAbstractTableModel):
    def __init__(self, rows=None):
        super().__init__()
        self.rows = rows or []

    def rowCount(self, parent=QModelIndex()):
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        value = self.rows[index.row()][COLUMNS[index.column()]]
        if role == Qt.DisplayRole:
            return str(value)
        if role == Qt.TextAlignmentRole and isinstance(value, int):
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return COLUMNS[section].replace("_", " ").title()
        return str(section + 1)

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


# ---------------- benchmark results window ----------------

class BenchmarkDialog(QDialog):
    def __init__(self, results, column, n, reverse, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Benchmark: {column} ({n:,} rows, {'desc' if reverse else 'asc'})")
        self.resize(860, 470)

        headers = ["Algorithm", "Complexity", "Stable", "Time (ms)", "Comparisons", "Swaps"]
        table = QTableWidget(len(results), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        timed = [m["time_ms"] for _, m in results if m]
        fastest = min(timed) if timed else None

        for r, (name, m) in enumerate(results):
            info = ALGORITHMS[name]
            vals = [name, info["complexity"], "Yes" if info["stable"] else "No"]
            if m:
                vals += [f"{m['time_ms']:,.2f}", f"{m['comparisons']:,}", f"{m['swaps']:,}"]
            else:
                vals += ["n/a", "n/a", "n/a"]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                if c >= 3:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if m and m["time_ms"] == fastest:
                    item.setBackground(QColor("#c8f7c5"))
                    item.setForeground(QColor("#000000"))
                table.setItem(r, c, item)

        note = QLabel("Green = fastest.  n/a = needs a numeric column.  "
                      "Counting/radix never compare keys, so they show 0 comparisons.  "
                      "Swaps = swaps + element moves/placements.")
        note.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addWidget(table)
        layout.addWidget(note)


# ---------------- main tab ----------------

class TableTab(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.dm = data_manager
        self.filtered = None          # None = no filter active (filters come in Step 6)
        self._scope_full = True
        self.worker = None
        self.bench = None

        # --- sort controls ---
        self.col_combo = QComboBox()
        for col in COLUMNS:
            self.col_combo.addItem(col.replace("_", " ").title(), col)
        self.col_combo.currentIndexChanged.connect(self._update_algorithms)

        self.algo_combo = QComboBox()
        self.algo_combo.setMinimumWidth(330)
        for name, info in ALGORITHMS.items():
            label = (f"{name}  |  {info['complexity']}  |  "
                     f"{'stable' if info['stable'] else 'not stable'}")
            if info["numeric_only"]:
                label += "  |  numeric columns only"
            self.algo_combo.addItem(label, name)

        self.order_combo = QComboBox()
        self.order_combo.addItems(["Ascending", "Descending"])

        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["Full dataset", "Current filtered results"])

        self.sort_btn = QPushButton("Sort")
        self.sort_btn.clicked.connect(self.start_sort)
        self.bench_btn = QPushButton("Benchmark")
        self.bench_btn.clicked.connect(self.start_benchmark)

        controls = QHBoxLayout()
        for text, widget in [("Column:", self.col_combo), ("Algorithm:", self.algo_combo),
                             ("Order:", self.order_combo), ("Scope:", self.scope_combo)]:
            controls.addWidget(QLabel(text))
            controls.addWidget(widget)
        controls.addWidget(self.sort_btn)
        controls.addWidget(self.bench_btn)
        controls.addStretch()

        self.result_label = QLabel("No sort run yet")
        sort_box = QGroupBox("Sorting")
        box_layout = QVBoxLayout(sort_box)
        box_layout.addLayout(controls)
        box_layout.addWidget(self.result_label)

        self.search_panel = SearchPanel()
        self.search_panel.search_requested.connect(self.do_search)
        self.search_panel.cleared.connect(self.clear_filter)

        self.filter_panel = FilterPanel()
        self.filter_panel.apply_requested.connect(self.do_filter)
        self.filter_panel.cleared.connect(self.clear_filter)

        self.controls = QTabWidget()
        self.controls.addTab(sort_box, "Sort")
        self.controls.addTab(self.search_panel, "Search")
        self.controls.addTab(self.filter_panel, "Advanced Filters")
        self.controls.setMaximumHeight(240)

        # --- table ---
        self.model = BookTableModel()
        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionBehavior(QTableView.SelectRows)
        self.view.setEditTriggers(QTableView.NoEditTriggers)
        self.view.horizontalHeader().setStretchLastSection(True)
        self.view.horizontalHeader().sectionClicked.connect(self.col_combo.setCurrentIndex)

        self.status = QLabel("No data loaded")

        layout = QVBoxLayout(self)
        layout.addWidget(self.controls)
        layout.addWidget(self.view)
        layout.addWidget(self.status)

        self._update_algorithms()
        self.load_data()

    # ---------- data ----------
    def load_data(self):
        try:
            self.dm.load()
        except FileNotFoundError:
            self.status.setText("books.csv not found. Run the scraper first.")
            return
        self.filtered = None
        self._refresh()
        self.view.resizeColumnsToContents()
        self.view.setColumnWidth(1, 300)   # title
        self.view.setColumnWidth(8, 250)   # publisher

    def _display_rows(self):
        return self.filtered if self.filtered is not None else self.dm.rows

    def _refresh(self):
        rows = self._display_rows()
        self.model.set_rows(rows)
        if self.filtered is None:
            self.status.setText(f"{len(rows):,} books")
        else:
            self.status.setText(f"{len(rows):,} of {len(self.dm.rows):,} books (filtered)")

    # ---------- controls ----------
    def _update_algorithms(self):
        """Grey out counting/radix/bucket when the chosen column is text."""
        numeric = DataManager.is_numeric(self.col_combo.currentData())
        model = self.algo_combo.model()
        for i in range(self.algo_combo.count()):
            name = self.algo_combo.itemData(i)
            model.item(i).setEnabled(numeric or not ALGORITHMS[name]["numeric_only"])
        if not model.item(self.algo_combo.currentIndex()).isEnabled():
            for i in range(self.algo_combo.count()):
                if model.item(i).isEnabled():
                    self.algo_combo.setCurrentIndex(i)
                    break

    def _set_busy(self, busy, message=""):
        self.sort_btn.setEnabled(not busy)
        self.bench_btn.setEnabled(not busy)
        if busy:
            self.status.setText(message)
        else:
            self._refresh()

    def _rows_for_scope(self):
        full = self.scope_combo.currentIndex() == 0
        return (self.dm.rows if full else self._display_rows()), full

    # ---------- sort ----------
    def start_sort(self):
        if not self.dm.rows:
            return
        column = self.col_combo.currentData()
        algo = self.algo_combo.currentData()
        reverse = self.order_combo.currentIndex() == 1
        rows, self._scope_full = self._rows_for_scope()
        self._last = (algo, column, len(rows))

        self._set_busy(True, f"Sorting {len(rows):,} rows with {algo}...")
        self.worker = SortWorker(rows, make_key(column), algo, reverse)
        self.worker.done.connect(self._sort_done)
        self.worker.start()

    def _sort_done(self, rows, metrics):
        if self._scope_full:
            self.dm.rows = rows
            if self.filtered is not None:   # keep the filtered view in the new order
                keep = {id(r) for r in self.filtered}
                self.filtered = [r for r in rows if id(r) in keep]
        elif self.filtered is not None:
            self.filtered = rows
        else:
            self.dm.rows = rows

        algo, column, n = self._last
        self.result_label.setText(
            f"{algo} on {n:,} rows by {column}:  {metrics['time_ms']:,.2f} ms  |  "
            f"{metrics['comparisons']:,} comparisons  |  {metrics['swaps']:,} swaps"
        )
        self._set_busy(False)

    # ---------- benchmark ----------
    def start_benchmark(self):
        if not self.dm.rows:
            return
        column = self.col_combo.currentData()
        reverse = self.order_combo.currentIndex() == 1
        rows, _ = self._rows_for_scope()

        self._set_busy(True, "Benchmarking...")
        self.bench = BenchmarkWorker(rows, make_key(column),
                                     DataManager.is_numeric(column), reverse)
        self.bench.progress.connect(lambda name: self.status.setText(f"Benchmarking: {name} ..."))
        self.bench.done.connect(lambda res: self._bench_done(res, column, len(rows), reverse))
        self.bench.start()

    def _bench_done(self, results, column, n, reverse):
        self._set_busy(False)
        BenchmarkDialog(results, column, n, reverse, self).exec_()

        # ---------- search / filter ----------
    def do_search(self, column, algorithm, text):
        if not self.dm.rows:
            return
        try:
            matches, m = run_search(self.dm.rows, column, text, algorithm,
                                    DataManager.is_numeric(column))
        except ValueError:
            self.search_panel.set_result("This column needs a whole number.")
            return
        self.filtered = matches
        self._refresh()
        extra = f"  |  sorted index built in {m['index_ms']:,.2f} ms" if m["index_ms"] is not None else ""
        self.search_panel.set_result(
            f"{algorithm}: {len(matches):,} match(es)  |  search time {m['time_ms']:.4f} ms  |  "
            f"{m['comparisons']:,} comparisons{extra}")

    def do_filter(self, conditions):
        if not self.dm.rows:
            return
        try:
            matches, ms = apply_filters(self.dm.rows, conditions)
        except ValueError as e:
            self.filter_panel.set_result(str(e))
            return
        self.filtered = matches
        self._refresh()
        self.filter_panel.set_result(
            f"{len(matches):,} of {len(self.dm.rows):,} rows match  ({ms:.2f} ms)")

    def clear_filter(self):
        self.filtered = None
        self._refresh()
        self.search_panel.set_result("")
        self.filter_panel.set_result("")
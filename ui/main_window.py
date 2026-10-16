from PyQt5.QtWidgets import QMainWindow, QTabWidget

from core.data_manager import DataManager
from ui.table_tab import TableTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Book Data Explorer")
        self.resize(1200, 700)

        self.dm = DataManager()

        tabs = QTabWidget()
        tabs.addTab(TableTab(self.dm), "Books")
        # the Scraper tab will be added here later
        self.setCentralWidget(tabs)
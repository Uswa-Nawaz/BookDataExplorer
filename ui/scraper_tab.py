"""Scraper tab: Start / Pause / Resume / Stop buttons and a progress bar.

This widget only handles the DISPLAY. It does not scrape anything itself.
When a button is clicked it emits a signal, and whoever owns the tab
(the main window, later the scraper) decides what to do.
"""
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (QHBoxLayout, QLabel, QProgressBar, QPushButton,
                             QVBoxLayout, QWidget)

# The three states the scraper can be in
IDLE = "idle"
RUNNING = "running"
PAUSED = "paused"


class ScraperTab(QWidget):
    # Signals: "announcements" sent to the outside world when a button is clicked
    start_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self, target_count=15000):
        super().__init__()
        self.target_count = target_count   # How many books we want to scrape
        self._build_ui()
        self.set_state(IDLE)
        self.set_progress(0)

    # ---------- building the layout ----------
    def _build_ui(self):
        # Buttons
        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.resume_button = QPushButton("Resume")
        self.stop_button = QPushButton("Stop")

        # Connect each click to a method of this class
        self.start_button.clicked.connect(self._on_start)
        self.pause_button.clicked.connect(self._on_pause)
        self.resume_button.clicked.connect(self._on_resume)
        self.stop_button.clicked.connect(self._on_stop)

        button_row = QHBoxLayout()
        for button in (self.start_button, self.pause_button,
                       self.resume_button, self.stop_button):
            button_row.addWidget(button)

        # Progress bar goes from 0 to the target number of books
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, self.target_count)

        # Labels
        self.status_label = QLabel()
        self.count_label = QLabel()

        # Stack everything vertically
        layout = QVBoxLayout()
        layout.addLayout(button_row)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.count_label)
        layout.addWidget(self.status_label)
        layout.addStretch()                # Pushes everything to the top
        self.setLayout(layout)

    # ---------- button handlers ----------
    # Each one updates the tab's state and tells the outside world.
    def _on_start(self):
        self.set_state(RUNNING)
        self.start_requested.emit()

    def _on_pause(self):
        self.set_state(PAUSED)
        self.pause_requested.emit()

    def _on_resume(self):
        self.set_state(RUNNING)
        self.resume_requested.emit()

    def _on_stop(self):
        self.set_state(IDLE)
        self.stop_requested.emit()

    # ---------- public methods (called from outside) ----------
    def set_state(self, state):
        """Enable only the buttons that make sense in the given state."""
        self.start_button.setEnabled(state == IDLE)
        self.pause_button.setEnabled(state == RUNNING)
        self.resume_button.setEnabled(state == PAUSED)
        self.stop_button.setEnabled(state in (RUNNING, PAUSED))
        self.status_label.setText(f"Status: {state.capitalize()}")

    def set_progress(self, scraped_count):
        """Update the progress bar and the 'x / y books' text."""
        self.progress_bar.setValue(scraped_count)
        self.count_label.setText(
            f"Books scraped: {scraped_count} / {self.target_count}")
"""Entry point of Book Data Explorer. Run this file to start the app."""
import sys

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)   # Every PyQt program needs exactly one QApplication
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())          # Start the event loop (keeps the window alive)


if __name__ == "__main__":
    main()
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

class StateBar(QWidget):
    
    undo_requested = pyqtSignal()
    redo_requested = pyqtSignal()
    reset_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.undo_button = QPushButton("Annulla ↩️")
        self.redo_button = QPushButton("Ripeti ↪️")
        self.reset_button = QPushButton("Ripristina 🔁")

        self.undo_button.clicked.connect(self.undo_requested.emit)
        self.redo_button.clicked.connect(self.redo_requested.emit)
        self.reset_button.clicked.connect(self.reset_requested.emit)

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.undo_button)
        layout.addWidget(self.redo_button)
        layout.addWidget(self.reset_button)
        self.setLayout(layout)

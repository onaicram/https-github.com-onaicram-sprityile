from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

class SaveBar(QWidget):
    
    load_requested = pyqtSignal()
    save_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.load_button = QPushButton("Carica 📂")
        self.save_button = QPushButton("Salva 💾")

        self.load_button.setFixedWidth(100)
        self.save_button.setFixedWidth(100)

        self.load_button.clicked.connect(self.load_requested.emit)
        self.save_button.clicked.connect(self.save_requested.emit)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.load_button)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

class SaveMenu(QWidget):
    
    load_requested = pyqtSignal()
    save_requested = pyqtSignal()
    export_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.load_button = QPushButton("Carica 📂")
        self.save_button = QPushButton("Salva 💾")
        self.export_button = QPushButton("Esporta Selezione 📤")

        self.load_button.setFixedWidth(100)
        self.save_button.setFixedWidth(100)
        self.export_button.setFixedWidth(120)
        self.export_button.setEnabled(False)

        self.load_button.clicked.connect(self.load_requested.emit)
        self.save_button.clicked.connect(self.save_requested.emit)
        self.export_button.clicked.connect(self.export_requested.emit)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self.load_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.export_button)
        self.setLayout(layout)

    def set_export_enabled(self, enabled: bool):
        self.export_button.setEnabled(enabled)

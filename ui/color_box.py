from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QColorDialog
from PyQt5.QtGui import QColor
from PyQt5.QtCore import pyqtSignal
from utils.controls_utils import ClickableLabel

class ColorBox(QWidget):
    
    color_changed = pyqtSignal(QColor)
    color_removed = pyqtSignal()
    color_copied = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_color = QColor(0, 0, 0)

        # Preview + HEX field
        self.color_preview = ClickableLabel()
        self.color_preview.setFixedSize(30, 18)
        self.color_preview.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid black;")
        self.color_preview.clicked.connect(self.choose_color)

        self.color_hex = QLineEdit(self.current_color.name().upper())
        self.color_hex.setFixedWidth(70)
        self.color_hex.setReadOnly(True)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.color_preview)
        top_layout.addWidget(self.color_hex)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Copia colore
        self.copy_button = QPushButton("Copia colore 📋")
        self.copy_button.clicked.connect(self.copy_color)

        # Rimuovi colore
        self.remove_button = QPushButton("Rimuovi colore ❌")
        self.remove_button.clicked.connect(self.remove_color)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.copy_button)
        layout.addWidget(self.remove_button)
        layout.addStretch()

        self.setLayout(layout)

    def choose_color(self):
        color = QColorDialog.getColor(initial=self.current_color, parent=self)
        if color.isValid():
            self.set_color(color)
            self.color_changed.emit(color)

    def set_color(self, color: QColor):
        self.current_color = color
        self.color_hex.setText(color.name().upper())
        self.color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
        self.color_changed.emit(color)

    def copy_color(self):
        hex_color = self.color_hex.text()
        self.color_copied.emit(hex_color)

    def remove_color(self):
        self.color_removed.emit()

    def clear_color(self):
        self.set_color(QColor(0, 0, 0))
        

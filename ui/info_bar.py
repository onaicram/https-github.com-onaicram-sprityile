from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt


class InfoBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.filename_label = QLabel("🗂️ File: Nessuno")
        self.filename_label.setFixedWidth(200)

        self.grid_label = QLabel("Griglia: OFF")
        self.mode_label = QLabel("SELEZIONE 🖱️")
        self.shortcut_label = QLabel()
        self.shortcut_label.setText("P: Disegna ✏️   |   O: Pick 🎯   |   L: Cancella 🗑️   |   G: Griglia 🟪 |   Esc: Seleziona 🖱️")

        layout = QHBoxLayout()
        
        layout.addWidget(self.mode_label)
        layout.addWidget(self.grid_label)
        layout.addWidget(self.shortcut_label)
        layout.setContentsMargins(5, 5, 5, 5)

        self.setLayout(layout)

    def set_mode(self, mode: str):
        mode_map = {
            "select": "SELEZIONE 🖱️",
            "ruler": "RIGHELLO 📏",
            "draw": "DISEGNO ✏️",
            "picker": "PICKER 🎯",
            "delete": "CANCELLA 🗑️"
        }
        self.mode_label.setText(mode_map.get(mode, "SELEZIONE 🖱️"))

    def set_grid_status(self, status: str):
        self.grid_label.setText(f"Griglia: {status}")

    

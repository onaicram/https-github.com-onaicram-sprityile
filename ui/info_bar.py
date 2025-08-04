from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt

class InfoBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.filename_label = QLabel("🗂️ File: Nessuno")
        self.filename_label.setFixedWidth(200)

        self.grid_label = QLabel("Griglia: OFF")
        self.grid_label.setAlignment(Qt.AlignLeft)
        
        self.mode_label = QLabel("SELEZIONE 🖱️")
        self.mode_label.setAlignment(Qt.AlignCenter)

        self.shortcut_label = QLabel()
        self.shortcut_label.setText("P: Disegna ✏️   |   O: Pick 🎯   |   L: Cancella 🗑️   |   Esc: Seleziona 🖱️")
        self.shortcut_label.setAlignment(Qt.AlignRight)

        layout = QHBoxLayout()
        
        layout.addStretch(8)
        layout.addWidget(self.mode_label)
        layout.addWidget(self.grid_label)
        layout.addStretch(2)
        layout.addWidget(self.shortcut_label)
        layout.setContentsMargins(5, 5, 5, 5)

        self.setLayout(layout)

    def set_mode(self, mode: str):
        mode_map = {
            "select": "SELEZIONE 🖱️",
            "draw": "DISEGNO ✏️",
            "picker": "PICKER 🎯",
            "delete": "CANCELLA 🗑️"
        }
        self.mode_label.setText(mode_map.get(mode, "SELEZIONE 🖱️"))

    def set_grid_status(self, status: str):
        self.grid_label.setText(f"Griglia: {status}")

    

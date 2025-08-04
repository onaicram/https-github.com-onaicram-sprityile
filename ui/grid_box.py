from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton
from PyQt5.QtCore import pyqtSignal

class GridBox(QWidget):
    grid_changed = pyqtSignal(bool, int)  

    def __init__(self, parent=None):
        super().__init__(parent)

        self.label = QLabel("Dimensione Tile:")
        
        self.grid_size_field = QSpinBox()
        self.grid_size_field.setRange(1, 256)
        self.grid_size_field.setValue(16)
        
        self.tile_layout = QHBoxLayout()
        self.tile_layout.addWidget(self.label)
        self.tile_layout.addWidget(self.grid_size_field)

        self.grid_button = QPushButton("Attiva griglia ⬜")
        self.grid_button.setCheckable(True)
        self.grid_button.setChecked(False)
        self.grid_button.clicked.connect(self.toggle_grid)

        layout = QVBoxLayout()
        layout.addLayout(self.tile_layout)
        layout.addWidget(self.grid_button)
        self.setLayout(layout)

    def toggle_grid(self):
        active = self.grid_button.isChecked()
        tile_size = self.grid_size_field.value()

        if active:
            self.grid_button.setText("Disattiva griglia 🟪")
        else:
            self.grid_button.setText("Attiva griglia ⬜")

        self.grid_changed.emit(active, tile_size)

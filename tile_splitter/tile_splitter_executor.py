from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QMessageBox, QScrollArea
)
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import QRect, Qt, QSize

from utils.controls_utils import save_pixmap_dialog


class TileSplitterWidget(QWidget):
    def __init__(self, source_pixmap: QPixmap, selected_coords: set, tile_size: int):
        super().__init__()
        self.setWindowTitle("Genera Tile")
        self.source_pixmap = source_pixmap
        self.selected_coords = selected_coords
        self.tile_size = tile_size
        self.generated_pixmap = None
        self.resize(300, 400)

        # Layout principale
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Anteprima dei tasselli selezionati
        self.preview_layout = QHBoxLayout()
        main_layout.addLayout(self.preview_layout)
        self.preview_selected_tiles()

        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignCenter)
        
        self.repeat_label = QLabel("Numero Tile:")
        self.repeat_label.setFixedWidth(60)

        self.repeat_field = QLineEdit("4")
        self.repeat_field.setFixedWidth(40)

        self.generate_button = QPushButton("Genera")
        self.generate_button.clicked.connect(self.generate_output)

        controls_layout.addWidget(self.repeat_label)
        controls_layout.addWidget(self.repeat_field)
        controls_layout.addWidget(self.generate_button)
        main_layout.addLayout(controls_layout)

        # Anteprima immagine generata
        self.output_preview_label = QLabel(" Anteprima immagine generata")
        self.output_preview_label.setAlignment(Qt.AlignCenter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.output_preview_label)
        self.scroll_area.setMinimumHeight(150)  

        main_layout.addWidget(self.scroll_area)

        self.save_button = QPushButton("Salva immagine")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_output)

        self.save_layout = QHBoxLayout()
        self.save_layout.addWidget(self.save_button)
        self.save_layout.setAlignment(Qt.AlignCenter)
        
        main_layout.addLayout(self.save_layout)

    def preview_selected_tiles(self):
        tile_size = self.tile_size
        scale = 8 # fattore di scala
        for x, y in sorted(self.selected_coords):
            rect = QRect(x * tile_size, y * tile_size, tile_size, tile_size)
            tile = self.source_pixmap.copy(rect)
            tile = tile.scaled(tile_size * scale, tile_size * scale, Qt.KeepAspectRatio)
            label = QLabel()
            label.setPixmap(tile)
            label.setFixedSize(tile.width() + 4, tile.height() + 4)
            self.preview_layout.addWidget(label)

    def generate_output(self):
        try:
            repeat_count = int(self.repeat_field.text())
            if repeat_count <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Errore", "Inserisci un numero valido di ripetizioni.")
            return

        tile_size = self.tile_size
        selected = sorted(self.selected_coords)
        rows = len(selected)
        width = tile_size * repeat_count
        height = tile_size * rows

        output = QPixmap(width, height)
        output.fill(Qt.transparent)  # trasparente o bianco

        painter = QPainter(output)

        for row, (x, y) in enumerate(selected):
            tile = self.source_pixmap.copy(x * tile_size, y * tile_size, tile_size, tile_size)
            for col in range(repeat_count):
                x_pos = col * tile_size
                y_pos = row * tile_size
                painter.drawPixmap(x_pos, y_pos, tile)
        painter.end()
        self.generated_pixmap = output
        self.save_button.setEnabled(True)
        scale_factor = 2
        size = QSize(output.width() * scale_factor, output.height() * scale_factor)
        scaled_preview = output.scaled(
            size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.output_preview_label.setPixmap(scaled_preview)

    def save_output(self):
        save_pixmap_dialog(self, self.generated_pixmap, "tasselli_generati")
        


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QScrollArea, QFileDialog, QGridLayout
)
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import QRect, Qt, QSize

from atlas.atlas_creator_widget import AtlasCreator

class TileSplitterWidget(QWidget):
    def __init__(self, source_pixmap: QPixmap, selected_coords: set, tile_size: int):
        super().__init__()
        self.setWindowTitle("Genera Tile")
        self.source_pixmap = source_pixmap
        self.selected_coords = selected_coords
        self.tile_size = tile_size
        self.generated_images = []

        self.resize(300, 400)

        # Layout principale
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.tile_layout = QGridLayout()
        self.view_selected_tiles()
        main_layout.addLayout(self.tile_layout)
        
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignCenter)

        self.repeat_label = QLabel("Numero Tile:")
        self.repeat_label.setFixedWidth(60)

        self.repeat_field = QLineEdit("4")
        self.repeat_field.setFixedWidth(40)

        self.generate_button = QPushButton("Genera")
        self.generate_button.clicked.connect(self.handle_generate)

        controls_layout.addWidget(self.repeat_label)
        controls_layout.addWidget(self.repeat_field)
        controls_layout.addWidget(self.generate_button)
        main_layout.addLayout(controls_layout)

        # Area anteprima immagini generate
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.preview_container = QWidget()
        self.preview_layout_output = QVBoxLayout(self.preview_container)
        self.scroll_area.setWidget(self.preview_container)
        self.scroll_area.setMinimumHeight(150)
        main_layout.addWidget(self.scroll_area)

        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignCenter)

        # Pulsante salva
        self.save_button = QPushButton("Salva immagini")
        self.save_button.setFixedWidth(100)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_images)

        self.load_button = QPushButton("Carica in Atlas")
        self.load_button.setFixedWidth(100)
        self.load_button.setEnabled(False)
        self.load_button.clicked.connect(self.load_into_atlas)

        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.load_button)

        main_layout.addLayout(self.button_layout)

    def view_selected_tiles(self):
        max_cols = 4
        tile_size = self.tile_size
        scale = 4
        for idx, (x, y) in enumerate(sorted(self.selected_coords)):
            rect = QRect(x * tile_size, y * tile_size, tile_size, tile_size)
            tile = self.source_pixmap.copy(rect)
            tile = tile.scaled(tile_size * scale, tile_size * scale, Qt.KeepAspectRatio)
            label = QLabel()
            label.setPixmap(tile)
            label.setFixedSize(tile.width() + 4, tile.height() + 4)
            
            row = idx // max_cols
            col = idx % max_cols

            self.tile_layout.addWidget(label, row, col)

    def handle_generate(self):
        try:
            repeat_count = int(self.repeat_field.text())
            if repeat_count <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Errore", "Inserisci un numero valido di ripetizioni.")
            return

        self.generated_images = self.generate_tile_images(repeat_count)
        self.update_output_preview()
        self.save_button.setEnabled(True)

    def generate_tile_images(self, repeat_count):
        
        tile_size = self.tile_size
        selected = sorted(self.selected_coords)
        self.generated_images = []  

        for x, y in selected:
            tile = self.source_pixmap.copy(x * tile_size, y * tile_size, tile_size, tile_size)
            result = QPixmap(tile_size * repeat_count, tile_size)
            result.fill(Qt.transparent)
            painter = QPainter(result)
            for i in range(repeat_count):
                painter.drawPixmap(i * tile_size, 0, tile)
            painter.end()
            self.generated_images.append(result)

        self.load_button.setEnabled(True)
        self.save_button.setEnabled(True)
        return self.generated_images
    
    def load_into_atlas(self):
        
        atlas = AtlasCreator()
        paths = [f"img_{i}" for i in range(len(self.generated_images))]
        atlas.view.show_images(self.generated_images, paths, start_idx=0)
        atlas.show()

    def update_output_preview(self):
        
        for i in reversed(range(self.preview_layout_output.count())):
            widget = self.preview_layout_output.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        scale = 2
        for img in self.generated_images:
            scaled = img.scaled(
                img.width() * scale, img.height() * scale,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            label = QLabel()
            label.setPixmap(scaled)
            label.setAlignment(Qt.AlignCenter)
            self.preview_layout_output.addWidget(label)

    def save_images(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleziona cartella")
        if not dir_path:
            return

        for i, pixmap in enumerate(self.generated_images):
            pixmap.save(f"{dir_path}/tile_{i}.png", "PNG")

        QMessageBox.information(self, "Salvato", "Immagini salvate con successo.")

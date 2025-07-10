from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QScrollArea, QFileDialog
)
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtCore import QRect, Qt, QSize

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

        # Pulsante salva
        self.save_button = QPushButton("Salva immagini")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_images)
        main_layout.addWidget(self.save_button)

    def preview_selected_tiles(self):
        tile_size = self.tile_size
        scale = 6
        for x, y in sorted(self.selected_coords):
            rect = QRect(x * tile_size, y * tile_size, tile_size, tile_size)
            tile = self.source_pixmap.copy(rect)
            tile = tile.scaled(tile_size * scale, tile_size * scale, Qt.KeepAspectRatio)
            label = QLabel()
            label.setPixmap(tile)
            label.setFixedSize(tile.width() + 4, tile.height() + 4)
            self.preview_layout.addWidget(label)

    def handle_generate(self):
        try:
            repeat_count = int(self.repeat_field.text())
            if repeat_count <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Errore", "Inserisci un numero valido di ripetizioni.")
            return

        self.generated_images = self.generate_repeated_tile_images(repeat_count)
        self.update_output_preview()
        self.save_button.setEnabled(True)

    def generate_repeated_tile_images(self, repeat_count):
        tile_size = self.tile_size
        output_images = []

        for x, y in sorted(self.selected_coords):
            rect = QRect(x * tile_size, y * tile_size, tile_size, tile_size)
            tile = self.source_pixmap.copy(rect)

            width = tile_size * repeat_count
            height = tile_size
            result = QPixmap(width, height)
            result.fill(Qt.transparent)

            painter = QPainter(result)
            for i in range(repeat_count):
                painter.drawPixmap(i * tile_size, 0, tile)
            painter.end()

            output_images.append(result)

        return output_images

    def update_output_preview(self):
        # Pulisce vecchie anteprime
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

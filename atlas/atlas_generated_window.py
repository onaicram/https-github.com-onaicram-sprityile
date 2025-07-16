import math
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene, QFileDialog, QMessageBox,
                             QWidget, QGraphicsPixmapItem, QPushButton, QHBoxLayout)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage
from PyQt5.QtCore import Qt, QRectF

from utils.controls_utils import CtrlDragMixin, apply_zoom
from utils.grid_utils import GridOverlayItem
from utils.meta_utils import MetaUtils
import os

class AtlasGeneratedWindow(QWidget):
    def __init__(self, tile_size, cols, rows, images_to_insert, edit_mdode=False, base_atlas=None, end_tile=None):
        super().__init__()
        self.setWindowTitle("Atlas Generato")
        self.setMinimumSize(400, 300)

        self.tile_size = tile_size
        self.cols = cols
        self.rows = rows
        self.images_to_insert = images_to_insert
        self.edit_mode = edit_mdode
        self.start_tile = [2,2]
        self.end_tile = end_tile
        self.base_atlas = base_atlas
        self.view = AtlasGeneratedView()

        self.grid_button = QPushButton("Attiva Griglia")
        self.grid_button.setCheckable(True)
        self.grid_button.setChecked(False)
        self.grid_button.setFixedWidth(100)
        self.grid_button.clicked.connect(self.toggle_grid)

        self.save_atlas_button = QPushButton("Salva")
        self.save_atlas_button.setFixedWidth(100)   
        self.save_atlas_button.clicked.connect(self.save_atlas)

        self_button_layout = QHBoxLayout()
        self_button_layout.addWidget(self.grid_button)
        self_button_layout.addWidget(self.save_atlas_button)
        self_button_layout.setAlignment(Qt.AlignCenter)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.view)
        self.layout.addLayout(self_button_layout)
        self.setLayout(self.layout)

        self.insert_images_into_atlas(tile_size, cols, rows, self.images_to_insert)

    
    def toggle_grid(self):
        if self.grid_button.isChecked():
            width = self.columns * self.tile_size
            height = self.rows * self.tile_size
            self.grid_item = GridOverlayItem(width, height, self.tile_size)
            self.view.scene.addItem(self.grid_item)
            self.grid_item.setZValue(10)
            self.grid_button.setText("Disattiva Griglia")
        else:
            if hasattr(self, "grid_item"):
                self.view.scene.removeItem(self.grid_item)
                del self.grid_item
                self.grid_button.setText("Attiva Griglia")


    def save_atlas(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salva Atlas", "atlas_", "PNG Files (*.png)")
        if path:
            success = self.view.pixmap_item.pixmap().save(path, "PNG")
            if not success:
                print("Errore durante il salvataggio dell'atlas.")
            else:
                print(f"Atlas salvato con successo in {path}")
                MetaUtils.save_meta(
                    image_path=path,
                    tile_size=self.tile_size,
                    editable=True,
                    cols=self.cols,
                    rows=self.rows,
                    start_tile=self.start_tile,
                    end_tile=getattr(self, "next_end_tile", [2, 2])
                )
                QMessageBox.information(self, "Salvataggio Meta Atlas", "Meta Atlas salvato con successo.")   


    def generate_checkerboard(self, tile_size, cols, rows):      
        width = tile_size * cols
        height = tile_size * rows
        image = QImage(width, height, QImage.Format_RGB32)
        p = QPainter(image)

        white = QColor(255, 255, 255)
        light_grey = QColor(200, 200, 200)
        black = QColor(0, 0, 0)

        for row in range(rows):
            for col in range(cols):
                x = col * tile_size
                y = row * tile_size

                # Riga o colonna guida
                if row == 0 or col == 0:
                    color = black if (row + col) % 2 == 0 else white
                else:
                    color = light_grey if (row + col) % 2 == 0 else white
                p.fillRect(x, y, tile_size, tile_size, color)
        p.end()
        return QPixmap.fromImage(image)
    
    
    def insert_images_into_atlas(self, tile_size, cols, rows, pixmaps):
        # 1. Base atlas (modifica o nuovo)
        if self.edit_mode and self.base_atlas and os.path.exists(self.base_atlas):
            base_pixmap = QPixmap(self.base_atlas)
        else:
            base_pixmap = self.generate_checkerboard(tile_size, cols, rows)

        image = base_pixmap.toImage()
        painter = QPainter(image)

        # 2. Tile iniziale per inserimento (default: 2,2)
        current_x_tile = self.end_tile[0] if self.end_tile else 2
        current_y_tile = self.end_tile[1] if self.end_tile else 2

        max_x_tile = current_x_tile
        max_y_tile = current_y_tile

        for pixmap in pixmaps:
            if pixmap.isNull():
                continue

            tiles_wide = math.ceil(pixmap.width() / tile_size)
            tiles_high = math.ceil(pixmap.height() / tile_size)

            # 3. Controlla se va a capo
            if current_x_tile + tiles_wide > cols:
                current_x_tile = 2  # torna all'inizio riga (salta margine)
                current_y_tile += tiles_high + 1  # va a capo + margine

            # 4. Disegna immagine
            x = current_x_tile * tile_size
            y = current_y_tile * tile_size
            painter.drawPixmap(x, y, pixmap)

            # 5. Aggiorna fine massima usata
            max_x_tile = max(max_x_tile, current_x_tile + tiles_wide)
            max_y_tile = max(max_y_tile, current_y_tile + tiles_high)

            # 6. Sposta cursore orizzontale per la prossima immagine
            current_x_tile += tiles_wide + 1  # +1 per margine visivo

        painter.end()

        # 7. Imposta la prossima tile disponibile come nuova end_tile
        self.next_end_tile = [current_x_tile, current_y_tile]

        # 8. Mostra il nuovo atlas
        final_pixmap = QPixmap.fromImage(image)
        self.view.set_pixmap(final_pixmap)



class AtlasGeneratedView(QGraphicsView, CtrlDragMixin):
    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor(220, 220, 220))
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.image_item = None

    def set_pixmap(self, pixmap):
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)

        self.setSceneRect(QRectF(pixmap.rect())) 
        self.centerOn(self.pixmap_item)

    def mousePressEvent(self, event):
        self.handle_drag_press(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.handle_drag_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.handle_drag_release(event)
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        apply_zoom(self, event, zoom_in=1.15)


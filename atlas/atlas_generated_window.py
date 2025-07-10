import math
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QGraphicsView, QGraphicsScene, QWidget, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage
from PyQt5.QtCore import Qt, QRectF

from utils.controls_utils import CtrlDragMixin, apply_zoom

class AtlasGeneratedWindow(QWidget):
    def __init__(self, tile_size, columns, rows, images_to_insert):
        super().__init__()
        self.setWindowTitle("Atlas Generato")
        self.setMinimumSize(400, 300)

        self.tile_size = tile_size
        self.columns = columns
        self.rows = rows
        self.images_to_insert = images_to_insert

        self.view = AtlasGeneratedView()
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.view)
        self.setLayout(self.layout)

        self.insert_images_into_atlas(tile_size, columns, rows, self.images_to_insert)
        

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

       
        checkerboard = self.generate_checkerboard(tile_size, cols, rows)

        image = checkerboard.toImage()
        painter = QPainter(image)

        current_x_tile = 2
        current_y_tile = 2

        for pixmap in pixmaps:
            if pixmap.isNull():
                continue

            tiles_wide = math.ceil(pixmap.width() / tile_size)
            tiles_high = math.ceil(pixmap.height() / tile_size)

            if current_x_tile + tiles_wide > cols:
                current_x_tile = 2
                current_y_tile += tiles_high

            x = current_x_tile * tile_size
            y = current_y_tile * tile_size
            painter.drawPixmap(x, y, pixmap)

            current_x_tile += tiles_wide

        painter.end()

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
        print("DEBUG: set_pixmap called")
        item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(item)

        self.setSceneRect(QRectF(pixmap.rect()))  # usa QRectF, non QRect!
        self.centerOn(item)

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


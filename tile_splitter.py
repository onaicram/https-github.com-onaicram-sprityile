from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGraphicsScene, QLineEdit, QGraphicsView,
                             QHBoxLayout, QPushButton, QLabel, QGraphicsPixmapItem, QMessageBox)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen 
from PyQt5.QtCore import Qt, QRectF


class TileSplitterWindow(QWidget):
    def __init__(self, source_pixmap: QPixmap):
        super().__init__()
        self.setWindowTitle("Gestione Tasselli")
        self.source_pixmap = source_pixmap
        self.viewer = GridGraphicsView()
        self.viewer.setScene(QGraphicsScene())
        self.viewer.pixmap_item = QGraphicsPixmapItem(self.source_pixmap)
        self.viewer.pixmap_item.setZValue(5)
        self.viewer.scene().addItem(self.viewer.pixmap_item)
        self.viewer.setSceneRect(QRectF(self.source_pixmap.rect()))
        self.viewer.centerOn(self.viewer.pixmap_item)
        self.viewer.resetTransform()
        self.resize(900, 700)  
        self.tile_size = 16
        self.init_ui()

    def init_ui(self):

        # Griglia UI
        self.grid_size_field = QLineEdit("16")
        self.grid_size_field.setFixedWidth(40)
        grid_label = QLabel("Dimensione griglia:")
        grid_label.setFixedWidth(100)
        self.grid_button = QPushButton("Mostra griglia")
        self.grid_button.setFixedWidth(100)
        self.grid_button.clicked.connect(self.draw_grid)

        grid_layout = QHBoxLayout()
        grid_layout.addWidget(grid_label)
        grid_layout.addWidget(self.grid_size_field)
        grid_layout.addWidget(self.grid_button)
        grid_layout.setAlignment(Qt.AlignCenter)

        # Layout complessivo
        layout = QVBoxLayout()
        layout.addLayout(grid_layout)
        layout.addWidget(self.viewer)
        self.setLayout(layout)

        # Adattamento iniziale
        self.adapt_to_image()
        self.viewer.draw_checkerboard()

    def adapt_to_image(self):
        view_width = self.viewer.viewport().width()
        view_height = self.viewer.viewport().height()
        pixmap_width = self.source_pixmap.width()
        pixmap_height = self.source_pixmap.height()
        scale_x = view_width / pixmap_width
        scale_y = view_height / pixmap_height
        scale = min(scale_x, scale_y) * 0.9
        
        self.viewer.resetTransform()
        self.viewer.scale(scale, scale)
        self.viewer.centerOn(self.viewer.pixmap_item)

    def draw_grid(self):
        try:
            tile_size = int(self.grid_size_field.text())
        except ValueError:
            QMessageBox.warning(self, "Errore", "Dimensione griglia non valida.")
            return

        self.viewer.draw_checkerboard(tile_size)
        self.viewer.draw_grid(tile_size)


class GridGraphicsView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QColor(220, 220, 220))
        self.setDragMode(QGraphicsView.NoDrag)
        self.pixmap_item = None

    def draw_checkerboard(self, tile_size=16):
        if self.pixmap_item is None:
            return

        # Rimuove eventuale checkerboard precedente
        if hasattr(self, "checker_item") and self.checker_item:
            self.scene().removeItem(self.checker_item)

        image_size = self.pixmap_item.pixmap().size()
        checker_pixmap = QPixmap(image_size)
        checker_pixmap.fill(Qt.transparent)

        painter = QPainter(checker_pixmap)
        color1 = QColor(200, 200, 200)
        color2 = QColor(255, 255, 255)

        for y in range(0, image_size.height(), tile_size):
            for x in range(0, image_size.width(), tile_size):
                rect = QRectF(x, y, tile_size, tile_size)
                painter.fillRect(rect, color1 if (x // tile_size + y // tile_size) % 2 == 0 else color2)

        painter.end()

        self.checker_item = QGraphicsPixmapItem(checker_pixmap)
        self.checker_item.setZValue(0)
        self.scene().addItem(self.checker_item)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.setCursor(Qt.ClosedHandCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        zoom_in = 1.15
        zoom_out = 1 / zoom_in
        zoom = zoom_in if event.angleDelta().y() > 0 else zoom_out
        self.scale(zoom, zoom)

    def draw_grid(self, tile_size=16):
        scene = self.scene()
        if self.pixmap_item is None:
            return
        
        if hasattr(self, "grid_items"):
            for item in self.grid_items:
                scene.removeItem(item)
        self.grid_items = []

        pixmap_rect = self.pixmap_item.pixmap().rect()
        width = pixmap_rect.width()
        height = pixmap_rect.height()

        pen = QPen(QColor(255, 100, 0, 255))
        pen.setWidthF(0.0)  # linea sottile e nitida

        # Linee verticali
        for x in range(0, width + 1, tile_size):
            line = scene.addLine(x, 0, x, height, pen)
            line.setZValue(10)
            self.grid_items.append(line)

        # Linee orizzontali
        for y in range(0, height + 1, tile_size):
            line = scene.addLine(0, y, width, y, pen)
            line.setZValue(10)
            self.grid_items.append(line)



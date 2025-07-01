from PyQt5.QtWidgets import (QWidget, QPushButton, QHBoxLayout, QVBoxLayout, 
                             QFileDialog, QLabel, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRectF

from controls_utils import save_pixmap_dialog, BasicDragMixin
from graphics_utils import draw_checkerboard_pixmap, auto_fit_view, apply_zoom, load_image_with_checker

class AtlasGraphicsView(QGraphicsView, BasicDragMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor(220, 220, 220))
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def wheelEvent(self, event):
        apply_zoom(self, event)

    def mousePressEvent(self, event):
        self.handle_drag_press(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.handle_drag_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.handle_drag_release(event)
        super().mouseReleaseEvent(event)

class AtlasManagerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestione Atlas")
        self.setMinimumSize(600, 400)
        self.view = AtlasGraphicsView()
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        
        # Basic Buttons
        self.load_button = QPushButton("Carica")
        self.load_button.clicked.connect(lambda: self.load_image())

        self.save_button = QPushButton("Salva")
        self.undo_button = QPushButton("Annulla")
        self.redo_button = QPushButton("Ripeti")
        self.reset_button = QPushButton("Ripristina")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.redo_button)
        button_layout.addWidget(self.reset_button)
        button_layout.setAlignment(Qt.AlignCenter)

        # Layout principale
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.view)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def load_image(self, pixmap: QPixmap = None):
        self.pixmap = load_image_with_checker(
            view=self.view,
            scene=self.scene,
            pixmap=pixmap,
            parent=self,
            tile_size=16
        )
        




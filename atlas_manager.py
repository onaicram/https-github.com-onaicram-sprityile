from PyQt5.QtWidgets import (QWidget, QPushButton, QHBoxLayout, QVBoxLayout, 
                             QFileDialog, QLabel, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRectF

from controls_utils import save_pixmap_dialog, BasicDragMixin
from graphics_utils import apply_zoom, load_image_with_checker
from states_utils import save_state, reset_image, undo, redo

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
        self.undo_stack = []
        self.redo_stack = []
        
        # Basic Buttons
        self.load_button = QPushButton("Carica")
        self.load_button.clicked.connect(lambda: self.load_image())

        self.save_button = QPushButton("Salva")
        self.save_button.clicked.connect(self.save_image)

        self.undo_button = QPushButton("Annulla")
        self.undo_button.clicked.connect(self.undo)

        self.redo_button = QPushButton("Ripeti")
        self.redo_button.clicked.connect(self.redo)

        self.reset_button = QPushButton("Ripristina")
        self.reset_button.clicked.connect(self.reset_image)

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

        self.original_pixmap = self.view.pixmap_item.pixmap().copy()
        save_state()
        
    def undo(self):
        undo(self.view.pixmap_item, self.undo_stack, self.redo_stack)

    def redo(self):
        redo(self.view.pixmap_item, self.undo_stack, self.redo_stack)

    def save_state(self):
        save_state(
            pixmap_item=self.view.pixmap_item,
            undo_stack=self.undo_stack,
            redo_stack=self.redo_stack
        )

    def reset_image(self):
        reset_image(
            pixmap_item=self.view.pixmap_item,
            original_pixmap=self.original_pixmap,
            undo_stack=self.undo_stack,
            redo_stack=self.redo_stack,
            parent=self
        )

    def save_image(self):
        if self.view.pixmap_item is None:
            return
        
        pixmap = self.view.pixmap_item.pixmap()
        save_pixmap_dialog(self, pixmap, "immagine")



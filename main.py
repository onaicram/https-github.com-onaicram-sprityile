import sys
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene,
    QMainWindow, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage
from PyQt5.QtCore import Qt, pyqtSignal

from tile_splitter.tile_splitter import TileSplitterWindow
from atlas.atlas_manager import AtlasManagerWindow
from utils.graphics_utils import load_image_with_checker
from utils.controls_utils import save_pixmap_dialog, apply_zoom, CtrlDragMixin,is_atlas_file
from utils.states_utils import save_state, undo_state, redo_state, reset_state
from utils.meta_utils import MetaUtils


class ImageViewer(QGraphicsView, CtrlDragMixin):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sprityle")
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = None
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QColor(220, 220, 220))  # Grigio chiaro uniforme
        self.checker_item = None

    color_picked = pyqtSignal(str)

    def mousePressEvent(self, event):
        if self.pixmap_item is None:
            return

        pos = self.mapToScene(event.pos())
        x, y = int(pos.x()), int(pos.y())

        if 0 <= x < self.pixmap_item.pixmap().width() and 0 <= y < self.pixmap_item.pixmap().height():
            image = self.pixmap_item.pixmap().toImage()
            color = image.pixelColor(x, y)
            hex_color = color.name().upper()
            self.color_picked.emit(hex_color)

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.undo_stack = []
        self.redo_stack = []
        self.current_tile_size = 16  # Dimensione predefinita dei tasselli

        self.setWindowTitle("Sprityle")

        self.view = ImageViewer()
        self.original_pixmap = None  
        self.view.color_picked.connect(self.show_color)

        self.tile_splitter_button = QPushButton("Gestione Tile")
        self.tile_splitter_button.setFixedWidth(120)
        self.tile_splitter_button.clicked.connect(self.open_tile_splitter)

        self.atlas_manager_button = QPushButton("Gestione Atlas")
        self.atlas_manager_button.setFixedWidth(120)
        self.atlas_manager_button.clicked.connect(self.open_atlas_manager)

        self.tile_splitter_layout= QHBoxLayout()
        self.tile_splitter_layout.addWidget(self.tile_splitter_button)
        self.tile_splitter_layout.addWidget(self.atlas_manager_button)
        self.tile_splitter_layout.setAlignment(Qt.AlignCenter)

        # Color 
        self.color_label = QLabel("Colore selezionato:")
        self.color_label.setMaximumWidth(90)

        self.color_field = QLineEdit("Nessun colore")
        self.color_field.setFixedWidth(100)
        self.color_field.setReadOnly(True)

        self.copy_button = QPushButton("Copia colore")
        self.copy_button.setFixedWidth(100)
        self.copy_button.clicked.connect(self.copy_color)

        self.remove_color_button = QPushButton("Rimuovi colore")
        self.remove_color_button.setFixedWidth(100)
        self.remove_color_button.clicked.connect(self.remove_selected_color)

        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_field)
        color_layout.addWidget(self.copy_button)
        color_layout.addWidget(self.remove_color_button)
        color_layout.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addLayout(self.tile_splitter_layout)
        layout.addWidget(self.view)
        layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(color_layout)

        # Buttons
        self.load_button = QPushButton("Carica")
        self.load_button.setMaximumWidth(120)
        self.load_button.clicked.connect(self.load_image)

        self.save_button = QPushButton("Salva")
        self.save_button.setFixedWidth(80)
        self.save_button.clicked.connect(self.save_image)

        self.undo_button = QPushButton("Annulla")
        self.undo_button.setFixedWidth(80)
        self.undo_button.clicked.connect(self.undo)

        self.redo_button = QPushButton("Ripeti")
        self.redo_button.setFixedWidth(80)
        self.redo_button.clicked.connect(self.redo)

        self.reset_button = QPushButton("Ripristina")
        self.reset_button.setFixedWidth(80)
        self.reset_button.clicked.connect(self.reset_image)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.redo_button)
        button_layout.addWidget(self.reset_button)
        button_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(button_layout)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


    def open_tile_splitter(self):
        pixmap = None
        if self.view.pixmap_item and not self.view.pixmap_item.pixmap().isNull():
            pixmap = self.view.pixmap_item.pixmap().copy()

        self.tile_splitter = TileSplitterWindow(pixmap)
        self.tile_splitter.show()

    def open_atlas_manager(self):
        pixmap = None
        if self.view.pixmap_item and not self.view.pixmap_item.pixmap().isNull():
            pixmap_item = self.view.pixmap_item
            pixmap = pixmap_item.pixmap()
            pixmap.path = getattr(pixmap_item, "path", None)
        self.atlas_manager = AtlasManagerWindow(edit_mode=is_atlas_file(pixmap.path) if pixmap and hasattr(pixmap, "path") else False)
        if pixmap is not None:
            self.atlas_manager.load_image(pixmap)
        self.atlas_manager.show()


    def remove_selected_color(self):
        if self.view.pixmap_item is None:
            return
        
        original_pixmap = self.view.pixmap_item.pixmap()
        image = original_pixmap.toImage().convertToFormat(QImage.Format_ARGB32) 

        color_hex = self.color_field.text()
        if not QColor.isValidColor(color_hex):
            return

        target_color = QColor(color_hex)
        changed = False
        
        for y in range(image.height()):
            for x in range(image.width()):
                if image.pixelColor(x, y) == target_color:
                    image.setPixelColor(x, y, QColor(0, 0, 0, 0))
                    changed = True

        if changed:
            self.view.pixmap_item.setPixmap(QPixmap.fromImage(image))
            self.save_state()

    def load_image(self):
    
        tile_size = int(self.current_tile_size)
            
        self.view.pixmap_item = load_image_with_checker(
            view=self.view,
            scene=self.view.scene,
            pixmap=None,
            parent=self,
            tile_size=tile_size 
        )

        if self.view.pixmap_item:
            self.original_pixmap = self.view.pixmap_item.pixmap().copy()
            self.undo_stack.clear()
            self.redo_stack.clear()       
            self.save_state()

    def save_image(self):
        if self.view.pixmap_item is None:
            return
        
        pixmap = self.view.pixmap_item.pixmap()
        path = save_pixmap_dialog(self, pixmap, "immagine")
        if path:
           MetaUtils.save_meta(
                path, self.current_tile_size, editable=True
            )
            
 

    def reset_image(self):
        reset_state(
            self.view.pixmap_item,
            self.original_pixmap,
            set(),
            self.undo_stack,
            self.redo_stack,
            restore_selection_fn=None,
            color_field=self.color_field,
            parent=self
        )

    def save_state(self):
        save_state(self.view.pixmap_item, set(), self.undo_stack, self.redo_stack)


    def undo(self):
        undo_state(
            self.view.pixmap_item,
            set(),  # Nessuna selezione in ImageViewer
            self.undo_stack,
            self.redo_stack,
            restore_selection_fn=None
        )

    def redo(self):
        redo_state(
            self.view.pixmap_item,
            set(),
            self.undo_stack,
            self.redo_stack,
            restore_selection_fn=None
        )

    def show_color(self, hex_color):
        self.color_field.setText(hex_color)


    def copy_color(self):
        color = self.color_field.text()
        if color and color != "Nessun colore":
            clipboard = QApplication.clipboard()
            clipboard.setText(color)
            QMessageBox.information(self, "Colore copiato", f"{color} copiato negli appunti.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())






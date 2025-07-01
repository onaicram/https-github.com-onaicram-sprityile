import sys
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QFileDialog, QMainWindow, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage
from PyQt5.QtCore import Qt, QRectF, pyqtSignal

from tile_splitter import TileSplitterWindow
from atlas_manager import AtlasManagerWindow
from graphics_utils import draw_checkerboard_pixmap, auto_fit_view, apply_zoom, load_image_with_checker
from controls_utils import save_pixmap_dialog, BasicDragMixin


class ImageViewer(QGraphicsView, BasicDragMixin):
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

        self.tile_splitter_button = QPushButton("Gestisci tasselli")
        self.tile_splitter_button.setFixedWidth(120)
        self.tile_splitter_button.clicked.connect(self.open_tile_splitter)

        self.atlas_manager_button = QPushButton("Gestisci Atlas")
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
        self.color_field.setFixedWidth(80)
        self.color_field.setReadOnly(True)

        self.copy_button = QPushButton("Copia")
        self.copy_button.setFixedWidth(80)
        self.copy_button.clicked.connect(self.copy_color)

        self.remove_color_button = QPushButton("Rimuovi colore")
        self.remove_color_button.setFixedWidth(120)
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
        if self.view.pixmap_item is None:
            QMessageBox.warning(self, "Errore", "Nessuna immagine caricata.")
            return

        pixmap = self.view.pixmap_item.pixmap().copy()

        self.tile_splitter = TileSplitterWindow(pixmap)
        self.tile_splitter.show()

    def open_atlas_manager(self):
        pixmap = None
        if self.view.pixmap_item and not self.view.pixmap_item.pixmap().isNull():
            pixmap = self.view.pixmap_item.pixmap().copy()

        self.atlas_manager = AtlasManagerWindow()
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
        
        self.original_pixmap = self.view.pixmap_item.pixmap().copy()
        self.undo_stack.clear()
        self.redo_stack.clear()       
        self.save_state()

    def save_image(self):
        if self.view.pixmap_item is None:
            return
        
        pixmap = self.view.pixmap_item.pixmap()
        save_pixmap_dialog(self, pixmap, "immagine")
            

    def reset_image(self):
        if self.original_pixmap and self.view.pixmap_item:
            # Ripristina l'immagine originale
            self.view.pixmap_item.setPixmap(QPixmap(self.original_pixmap))

            # Pulisce gli stack di undo e redo
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.save_state()

            # Aggiorna lo stato visivo e informa l'utente
            self.color_field.setText("Nessun colore")
            QMessageBox.information(self, "Reset", "Immagine ripristinata.")


    def save_state(self):
        if self.view.pixmap_item:
            pixmap = self.view.pixmap_item.pixmap().copy()
            self.undo_stack.append(pixmap)
            self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) > 1:
            current = self.undo_stack.pop()
            self.redo_stack.append(current)
            prev = self.undo_stack[-1]
            self.view.pixmap_item.setPixmap(prev)

    def redo(self):
        if self.redo_stack:
            next_state = self.redo_stack.pop()
            self.undo_stack.append(next_state)
            self.view.pixmap_item.setPixmap(next_state)


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
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec_())

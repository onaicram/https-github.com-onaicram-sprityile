from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGraphicsScene, QLineEdit, QGraphicsView,
                             QHBoxLayout, QPushButton, QLabel, QGraphicsPixmapItem, QMessageBox)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QRectF

from tile_splitter.tile_splitter_widget import TileSplitterWidget
from utils.graphics_utils import draw_checkerboard_pixmap, draw_grid_lines, auto_fit_view, apply_zoom
from utils.controls_utils import CtrlDragMixin


class TileSplitterWindow(QWidget):
    def __init__(self, source_pixmap: QPixmap):
        super().__init__()
        self.setWindowTitle("Gestione Tasselli")
        self.source_pixmap = source_pixmap
        self.view = GridGraphicsView()
        self.view.setScene(QGraphicsScene())
        self.view.pixmap_item = QGraphicsPixmapItem(self.source_pixmap)
        self.view.pixmap_item.setZValue(5)
        self.view.scene().addItem(self.view.pixmap_item)
        self.view.setSceneRect(QRectF(self.source_pixmap.rect()))
        self.view.centerOn(self.view.pixmap_item)
        self.view.resetTransform()
        self.resize(800, 600)  
        self.tile_size = 16
        self.init_ui()

    def init_ui(self):

        # Griglia UI
        self.grid_size_field = QLineEdit("16")
        self.grid_size_field.setFixedWidth(40)
        grid_label = QLabel("Dimensione griglia:")
        grid_label.setFixedWidth(100)
        
        self.grid_button = QPushButton("Attiva griglia")
        self.grid_button.setCheckable(True)
        self.grid_button.setChecked(False)
        self.grid_button.setFixedWidth(100)
        self.grid_button.clicked.connect(self.draw_grid)

        self.separator_button = QPushButton("Avvia separazione")
        self.separator_button.setFixedWidth(100)
        self.separator_button.clicked.connect(self.open_tile_splitter)

        grid_layout = QHBoxLayout()
        grid_layout.addWidget(grid_label)
        grid_layout.addWidget(self.grid_size_field)
        grid_layout.addWidget(self.grid_button)
        grid_layout.addWidget(self.separator_button)
        grid_layout.setAlignment(Qt.AlignCenter)

        # Layout complessivo
        layout = QVBoxLayout()
        layout.addLayout(grid_layout)
        layout.addWidget(self.view)
        self.setLayout(layout)

        # Adattamento iniziale
        auto_fit_view(self.view, self.source_pixmap)
        self.view.draw_checkerboard()

    def draw_grid(self):
        try:
            tile_size = int(self.grid_size_field.text())
            self.tile_size = tile_size
            self.view.set_tile_size(tile_size)
        except ValueError:
            QMessageBox.warning(self, "Errore", "Dimensione griglia non valida.")
            return
        
        self.view.draw_checkerboard(tile_size)

        if self.grid_button.isChecked():
            self.grid_button.setText("Disattiva griglia")
            self.view.grid_visible = True
            self.view.draw_grid(tile_size)
        else:
            self.grid_button.setText("Attiva griglia")
            self.view.grid_visible = False
            self.view.clear_grid()

    def open_tile_splitter(self):
        if not hasattr(self.view, "selected_coords") or not self.view.selected_coords:
            QMessageBox.warning(self, "Errore", "Nessun tassello selezionato.")
            return

        try:
            tile_size = int(self.grid_size_field.text())
        except ValueError:
            QMessageBox.warning(self, "Errore", "Dimensione griglia non valida.")
            return

        # Salviamo l'istanza come attributo per evitare che venga distrutta
        self.separator_window = TileSplitterWidget(
            source_pixmap=self.source_pixmap,
            selected_coords=self.view.selected_coords,
            tile_size=tile_size
        )
        self.separator_window.show()


class GridGraphicsView(QGraphicsView, CtrlDragMixin):
    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QColor(220, 220, 220))
        self.setDragMode(QGraphicsView.NoDrag)
        self.pixmap_item = None
        self.tile_size = 16
        self.selected_tiles = []
        self.selected_coords = set()
        self.grid_visible = False

    def draw_checkerboard(self, tile_size=16):
        if self.pixmap_item is None:
            return

        # Rimuove eventuale checkerboard precedente
        if hasattr(self, "checker_item") and self.checker_item:
            self.scene().removeItem(self.checker_item)

        image_size = self.pixmap_item.pixmap().size()
        checkerboard = draw_checkerboard_pixmap(image_size.width(), image_size.height(), tile_size)
        
        self.checker_item = QGraphicsPixmapItem(checkerboard)
        self.checker_item.setZValue(0)
        self.scene().addItem(self.checker_item)

    def clear_grid(self):
        if hasattr(self, "grid_items"):
            for item in self.grid_items:
                self.scene().removeItem(item)
            self.grid_items.clear()


    def mousePressEvent(self, event):
        if self.grid_visible:
            if event.button() == Qt.LeftButton:
                if event.modifiers() & Qt.ControlModifier:
                    # Ctrl premuto → pan
                    self.handle_drag_press(event)
                else:    
                    pos = self.mapToScene(event.pos())
                    x = int(pos.x() // self.tile_size)
                    y = int(pos.y() // self.tile_size)

                    # BLOCCO: evita selezione fuori immagine
                    if not self.pixmap_item.pixmap().rect().contains(int(pos.x()), int(pos.y())):
                        return
                    
                    coord = (x, y)

                    if coord in self.selected_coords:
                        # Deseleziona
                        self.selected_coords.remove(coord)
                        self._remove_tile_marker(coord)
                    else:
                        # Seleziona
                        self.selected_coords.add(coord)
                        self._highlight_tile(coord)         
        else:
            self.handle_drag_press(event)
                
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.handle_drag_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.handle_drag_release(event)
        super().mouseReleaseEvent(event)


    def _highlight_tile(self, coord):
        x, y = coord
        rect = QRectF(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
        
        item = self.scene().addRect(rect, QPen(Qt.NoPen), QColor(255, 165, 0, 150))  # Arancione tenue
        item.setZValue(9)  # Sotto le linee della griglia (che stanno a 10)
        
        if not hasattr(self, "tile_markers"):
            self.tile_markers = {}
        self.tile_markers[coord] = item

    def _remove_tile_marker(self, coord):
        if hasattr(self, "tile_markers") and coord in self.tile_markers:
            self.scene().removeItem(self.tile_markers[coord])
            del self.tile_markers[coord]
   
    def set_tile_size(self, size):
        self.tile_size = size


    def wheelEvent(self, event):
        apply_zoom(self, event, zoom_in=1.15)

    def draw_grid(self, tile_size=16):
        self.grid_visible = True
        scene = self.scene()
        if self.pixmap_item is None:
            return
        
        if hasattr(self, "grid_items"):
            for item in self.grid_items:
                scene.removeItem(item)
        self.grid_items = []

        pixmap_rect = self.pixmap_item.pixmap().rect()
        self.grid_items = draw_grid_lines(
            scene, pixmap_rect.width(), pixmap_rect.height(), tile_size)
        



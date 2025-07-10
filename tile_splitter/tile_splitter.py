from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGraphicsScene, QGraphicsView, QFileDialog,
                             QHBoxLayout, QPushButton, QLabel, QGraphicsPixmapItem, QMessageBox, QSpinBox, QShortcut)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QKeySequence
from PyQt5.QtCore import Qt, QRectF

from tile_splitter.tile_splitter_executor import TileSplitterWidget
from utils.graphics_utils import draw_checkerboard_for_view, auto_fit_view
from utils.controls_utils import apply_zoom, CtrlDragMixin
from utils.grid_utils import draw_grid_ui
from utils.states_utils import save_state

class TileSplitterWindow(QWidget):
    def __init__(self, source_pixmap: QPixmap= None):
        super().__init__()
        self.setWindowTitle("Gestione Tile")
        self.view = GridGraphicsView()
        self.view.setScene(QGraphicsScene())

        if source_pixmap:
            self.set_pixmap(source_pixmap)
        else:
            self.load_image()

        
        self.resize(800, 600)  
        self.tile_size = 16
        self.grid_shortcut = QShortcut(QKeySequence("G"), self)
        self.grid_shortcut.activated.connect(lambda: self.grid_button.click())
        
        
        # Griglia UI
        self.load_button  = QPushButton("Carica immagine")
        self.load_button.setFixedWidth(100)
        self.load_button.clicked.connect(self.load_image)
        
        grid_label = QLabel("Dimensione Tile:")
        grid_label.setFixedWidth(80)

        self.grid_size_field = QSpinBox()
        self.grid_size_field.setRange(1, 256)
        self.grid_size_field.setValue(16)
        self.grid_size_field.setFixedWidth(40)
        
        self.grid_button = QPushButton("Griglia")
        self.grid_button.setCheckable(True)
        self.grid_button.setChecked(False)
        self.grid_button.setFixedWidth(100)
        self.grid_button.clicked.connect(lambda: draw_grid_ui(self.view, self.grid_size_field, self.grid_button))

        self.separator_button = QPushButton("Avvia separazione")
        self.separator_button.setFixedWidth(100)
        self.separator_button.clicked.connect(self.open_tile_splitter)

        grid_layout = QHBoxLayout()
        grid_layout.addWidget(self.load_button)
        grid_layout.addWidget(grid_label)
        grid_layout.addWidget(self.grid_size_field)
        grid_layout.addWidget(self.grid_button)
        grid_layout.addWidget(self.separator_button)
        grid_layout.setAlignment(Qt.AlignCenter)

        # Layout complessivo
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addLayout(grid_layout)
        self.setLayout(layout)

        draw_checkerboard_for_view(self.view, self.tile_size)


    def set_pixmap(self, pixmap: QPixmap):
        self.source_pixmap = pixmap
        self.view.pixmap_item = QGraphicsPixmapItem(self.source_pixmap)
        self.view.pixmap_item.setZValue(5)
        self.view.scene().addItem(self.view.pixmap_item)
        self.view.setSceneRect(QRectF(self.source_pixmap.rect()))
        self.view.centerOn(self.view.pixmap_item)
        auto_fit_view(self.view, self.source_pixmap)
        

    def open_tile_splitter(self):
        if not hasattr(self.view, "selected_coords") or not self.view.selected_coords:
            QMessageBox.warning(self, "Errore", "Nessun tile selezionato.")
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

    
    def load_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "Carica immagine", "", "Immagini (*.png *.jpg *.bmp)")
        if file:
            pixmap = QPixmap(file)
            if not pixmap.isNull():
                self.set_pixmap(pixmap)
                
                


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

                    if hasattr(self.window(), "undo_stack") and self.pixmap_item:
                        save_state(
                            self.pixmap_item,
                            self.selected_coords,
                            self.window().undo_stack,
                            self.window().redo_stack
                        )

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

    



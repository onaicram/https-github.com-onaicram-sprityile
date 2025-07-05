from PyQt5.QtWidgets import (QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox,
                             QGraphicsScene, QLabel, QSpinBox, QSizePolicy, QGraphicsRectItem)
from PyQt5.QtGui import QPixmap, QPen, QColor, QPainter
from PyQt5.QtCore import Qt, QRectF

from utils.controls_utils import save_pixmap_dialog, ShiftDragRectSelectMixin, get_snapped_rect
from utils.graphics_utils import load_image_with_checker
from utils.states_utils import save_state, undo_state, redo_state, reset_state
from utils.grid_utils import draw_grid_ui
from tile_splitter.tile_splitter import GridGraphicsView


class AtlasManagerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestione Atlas")
        self.setMinimumSize(900, 700)
        self.view = AtlasGraphicsView()
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.grid_visible = True
        self.grid_tile_size = 16
        self.undo_stack = []
        self.redo_stack = []

        # Basic Buttons
        self.load_button = QPushButton("Carica")
        self.load_button.clicked.connect(lambda: self.load_image())

        self.save_button = QPushButton("Salva")
        self.save_button.clicked.connect(self.save_image)

        self.undo_button = QPushButton("Annulla")
        self.undo_button.clicked.connect(self.on_undo)

        self.redo_button = QPushButton("Ripeti")
        self.redo_button.clicked.connect(self.on_redo)

        self.reset_button = QPushButton("Ripristina")
        self.reset_button.clicked.connect(self.on_reset)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.undo_button)
        button_layout.addWidget(self.redo_button)
        button_layout.addWidget(self.reset_button)
        button_layout.setAlignment(Qt.AlignCenter)

        # Griglia UI
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

        self.save_selection_button = QPushButton("Salva selezione")
        self.save_selection_button.setFixedWidth(100)
        self.save_selection_button.clicked.connect(lambda: self.save_selection())

        grid_layout = QHBoxLayout()
        grid_layout.addWidget(grid_label)
        grid_layout.addWidget(self.grid_size_field)
        grid_layout.addWidget(self.grid_button)
        grid_layout.addWidget(self.save_selection_button)
        grid_layout.setAlignment(Qt.AlignCenter)

        # Layout principale
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.view, stretch=1)
        main_layout.addLayout(grid_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def on_undo(self):
        undo_state(
        self.view.pixmap_item,
        self.view.selected_coords,
        self.undo_stack,
        self.redo_stack,
        self.view.restore_selection
    )
        

    def on_redo(self):
        redo_state(
        self.view.pixmap_item,
        self.view.selected_coords,
        self.undo_stack,
        self.redo_stack,
        self.view.restore_selection
    )
        
    def on_reset(self):
        reset_state(
        self.view.pixmap_item,
        self.original_pixmap,
        self.view.selected_coords,
        self.undo_stack,
        self.redo_stack,
        self.view.restore_selection
    )

        

    def load_image(self, pixmap: QPixmap = None):
        self.pixmap = load_image_with_checker(
            view=self.view,
            scene=self.scene,
            pixmap=pixmap,
            parent=self,
            tile_size=16
        )

        self.view.pixmap_item = self.pixmap
        self.original_pixmap = self.view.pixmap_item.pixmap().copy()
        self.view.setSceneRect(QRectF(self.pixmap.pixmap().rect()))
        self.undo_stack.clear()
        self.redo_stack.clear()

        print(f"[LOAD IMAGE] Pixmap caricato: {self.pixmap.pixmap().size()}")

        save_state(
            self.view.pixmap_item,
            self.view.selected_coords,
            self.undo_stack,
            self.redo_stack
        )


    def save_selection(self, rect: QRectF = None):
        if rect is None:
            rect = getattr(self.view, "last_selection_rect", None)

        if not isinstance(rect, QRectF):
            QMessageBox.warning(self, "Errore", "Nessuna selezione disponibile.")
            return

        if not self.view.pixmap_item:
            return

        # Allinea il rettangolo ai tile interi
        rect = get_snapped_rect(rect, self.grid_size_field.value())

        x = int(rect.left())
        y = int(rect.top())
        w = int(rect.width())
        h = int(rect.height())

        source_pixmap = self.view.pixmap_item.pixmap()
        selected_pixmap = source_pixmap.copy(x, y, w, h)

        save_pixmap_dialog(self, selected_pixmap, "immagine")


    def save_image(self):
        if self.view.pixmap_item is None:
            return
        
        pixmap = self.view.pixmap_item.pixmap()
        save_pixmap_dialog(self, pixmap, "immagine")


class AtlasGraphicsView(GridGraphicsView, ShiftDragRectSelectMixin):
    def __init__(self):
        super().__init__()
        self.drag_selecting = False
        self.drag_start_pos = None
        self.selection_rect_item: QGraphicsRectItem = None
        self.last_selection_rect: QRectF = QRectF()
        self.selected_coords = set()
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()


    def mousePressEvent(self, event):
        if self.grid_visible and self.handle_shift_press(event, self.scene(), self.pixmap_item):
            return
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        self.handle_shift_move(event)
        super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        self.handle_shift_release(event, self.scene(), self.select_tiles_in_rect)
        super().mouseReleaseEvent(event)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D:
            self.erase_selected_tiles()
        else:
            super().keyPressEvent(event)


    def select_tiles_in_rect(self, rect: QRectF):

        print(f"[SELECT RECT] Nuova selezione rettangolare: {rect}")

        self.last_selection_rect = rect

        for coord in list(self.selected_coords):
            self._remove_tile_marker(coord)
        self.selected_coords.clear()
        
        x_start = int(rect.left()) // self.tile_size
        y_start = int(rect.top()) // self.tile_size
        x_end = int(rect.right()) // self.tile_size
        y_end = int(rect.bottom()) // self.tile_size

        for y in range(y_start, y_end + 1):
            for x in range(x_start, x_end + 1):
                coord = (x, y)
                if coord not in self.selected_coords:
                    self.selected_coords.add(coord)
                    self._highlight_tile(coord)

        print(f"[SELECT RECT] Tiles selezionati: {self.selected_coords}")

        # Salva lo stato
        if hasattr(self.window(), "undo_stack") and self.pixmap_item:
            save_state(
                self.pixmap_item,
                self.selected_coords,
                self.window().undo_stack,
                self.window().redo_stack
            )


    def erase_selected_tiles(self):
        if not self.pixmap_item:
            return
        if not self.selected_coords:
            return
        
        if hasattr(self.parent(), "undo_stack") and self.pixmap_item:
            save_state(
                self.pixmap_item,
                self.selected_coords,
                self.parent().undo_stack,
                self.parent().redo_stack
            )

        # Cancella pixel selezionati
        original = self.pixmap_item.pixmap()
        image = original.toImage()
        for x, y in self.selected_coords:
            px, py = x * self.tile_size, y * self.tile_size
            for dx in range(self.tile_size):
                for dy in range(self.tile_size):
                    image.setPixelColor(px + dx, py + dy, Qt.transparent)
        new_pixmap = QPixmap.fromImage(image)
        self.pixmap_item.setPixmap(new_pixmap)

        # Rimuove i marker visivi (rettangoli arancioni)
        for coord in list(self.selected_coords):  # fai una copia per sicurezza
            self._remove_tile_marker(coord)

        # Svuota selezione logica
        self.selected_coords.clear()

        # Rimuove eventuale rettangolo di selezione multipla
        if getattr(self, "selection_rect_item", None):
            self.scene().removeItem(self.selection_rect_item)
            self.selection_rect_item = None

        self.viewport().update()

        if hasattr(self.window(), "undo_stack"):
            save_state(
                self.pixmap_item,
                set(),  # selezione svuotata
                self.window().undo_stack,
                self.window().redo_stack
            )


    def restore_selection(self, coords: set):
        # Pulisce tutto
        for coord in list(self.selected_coords):
            self._remove_tile_marker(coord)
        self.selected_coords.clear()

        # Reimposta selezione
        for coord in coords:
            self.selected_coords.add(coord)
            self._highlight_tile(coord)

        self.viewport().update()
        
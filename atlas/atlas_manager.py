from PyQt5.QtWidgets import (QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QMessageBox,
                             QGraphicsScene, QLabel, QSpinBox, QSizePolicy, QGraphicsRectItem, QShortcut)
from PyQt5.QtGui import QPixmap, QKeySequence, QPainter, QColor
from PyQt5.QtCore import Qt, QRectF

from utils.controls_utils import save_pixmap_dialog, ShiftDragRectSelectMixin, get_snapped_rect, is_atlas_file
from utils.graphics_utils import load_image_with_checker
from utils.states_utils import save_state, undo_state, redo_state, reset_state
from utils.grid_utils import draw_grid_ui
from tile_splitter.tile_splitter import GridGraphicsView
from tile_splitter.tile_splitter_executor import TileSplitterWidget
from atlas.atlas_creator_widget import AtlasCreator 
from utils.meta_utils import MetaUtils

class AtlasManagerWindow(QWidget):
    def __init__(self, edit_mode=False):
        super().__init__()
        self.setWindowTitle("Gestione Atlas")
        self.setMinimumSize(900, 700)
        self.view = AtlasGraphicsView()
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.edit_mode = edit_mode
        self.grid_visible = True
        self.grid_tile_size = 16
        self.undo_stack = []
        self.redo_stack = []
        self.grid_shortcut = QShortcut(QKeySequence("G"), self)
        self.grid_shortcut.activated.connect(lambda: self.grid_button.click())

        self.mode_label = QLabel("🟢 MODIFICA" if self.edit_mode else "⚪ NUOVO")
        self.mode_label.setAlignment(Qt.AlignCenter)

        tile_extraction_button = QPushButton("Separa Tile")
        tile_extraction_button.setFixedWidth(100)
        tile_extraction_button.clicked.connect(self.open_tile_splitter)

        self.atlas_creator_button = QPushButton("Crea Atlas")
        self.atlas_creator_button.setFixedWidth(100)
        self.atlas_creator_button.clicked.connect(self.open_atlas_creator)

        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(self.atlas_creator_button)
        top_bar_layout.addWidget(tile_extraction_button)
        top_bar_layout.setAlignment(Qt.AlignCenter)

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
        main_layout.addWidget(self.mode_label)
        main_layout.addLayout(top_bar_layout)
        main_layout.addWidget(self.view, stretch=1)
        main_layout.addLayout(grid_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

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
            source_pixmap=self.original_pixmap,
            selected_coords=self.view.selected_coords,
            tile_size=tile_size
        )
        self.separator_window.show()

    
    def open_atlas_creator(self):
        atlas_name = ""
        path = None
        
        if hasattr(self, "pixmap") and self.pixmap:
            path = getattr(self.pixmap, "path", None)
            if path and is_atlas_file(path):
                atlas_name = path.split("/")[-1]

        self.atlas_creator = AtlasCreator(edit_mode=self.edit_mode, atlas_name=atlas_name, atlas_path=path)
        self.atlas_creator.edit_mode = self.edit_mode

        if hasattr(self, "pixmap") and self.pixmap:
            path = getattr(self.pixmap, "path", None)
            if path:
                pixmap = self.pixmap.pixmap()
                self.atlas_creator.load_images_from_pixmaps_and_paths([pixmap], [path])

        self.atlas_creator.show()


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

        if self.pixmap:
            self.view.pixmap_item = self.pixmap
            self.original_pixmap = self.view.pixmap_item.pixmap().copy()
            self.view.setSceneRect(QRectF(self.pixmap.pixmap().rect()))
            self.undo_stack.clear()
            self.redo_stack.clear()

            save_state(
                self.view.pixmap_item,
                self.view.selected_coords,
                self.undo_stack,
                self.redo_stack
            )

            if hasattr(self.pixmap, "path"):

                # se l'img caricata ha prefisso 
                self.edit_mode = is_atlas_file(self.pixmap.path)

                # modalità Edit attiva
                if is_atlas_file(self.pixmap.path):
                    self.atlas_creator_button.setText("Modifica Atlas")
                    self.mode_label.setText("🟢 MODIFICA")
                else:
                    self.atlas_creator_button.setText("Crea Atlas")
                    self.mode_label.setText("⚪ NUOVO")
                 
            else:
                self.pixmap.path = getattr(self.view.pixmap_item, "path", None)


    def save_selection(self, rect: QRectF = None):
        tile_size = self.grid_size_field.value()
        source_pixmap = self.view.pixmap_item.pixmap()

        selected_tiles = set(getattr(self.view, "selected_coords", set()))

        # Se c'è un rettangolo, includi tutti i tile interni
        if rect is None:
            rect = getattr(self.view, "last_selection_rect", None)

        if isinstance(rect, QRectF):
            rect = get_snapped_rect(rect, tile_size)
            left = int(rect.left()) // tile_size
            top = int(rect.top()) // tile_size
            right = int((rect.right() - 1)) // tile_size
            bottom = int((rect.bottom() - 1)) // tile_size
            for x in range(left, right + 1):
                for y in range(top, bottom + 1):
                    selected_tiles.add((x, y))

        if not selected_tiles:
            QMessageBox.warning(self, "Errore", "Nessuna selezione disponibile.")
            return

        # Calcola bounding box dei tile selezionati
        min_x = min(x for x, _ in selected_tiles)
        min_y = min(y for _, y in selected_tiles)
        max_x = max(x for x, _ in selected_tiles)
        max_y = max(y for _, y in selected_tiles)

        width = (max_x - min_x + 1) * tile_size
        height = (max_y - min_y + 1) * tile_size

        # Immagine finale trasparente
        final_pixmap = QPixmap(width, height)
        final_pixmap.fill(Qt.transparent)

        # Disegna solo i tile selezionati
        painter = QPainter(final_pixmap)
        for x, y in selected_tiles:
            src_x = x * tile_size
            src_y = y * tile_size
            tile = source_pixmap.copy(src_x, src_y, tile_size, tile_size)

            dest_x = (x - min_x) * tile_size
            dest_y = (y - min_y) * tile_size
            painter.drawPixmap(dest_x, dest_y, tile)
        painter.end()

        save_pixmap_dialog(self, final_pixmap, "selezione_atlas")

    
    def save_image(self):
        if self.view.pixmap_item is None:
            return

        pixmap = self.view.pixmap_item.pixmap()
        path = save_pixmap_dialog(self, pixmap, "atlas_")
        if not path:
            return

        # Recupera i dati da UI
        tile_size = self.grid_size_field.value()

        MetaUtils.save_meta(
            path, 
            tile_size, 
            editable=True
        )

        QMessageBox.information(self, "Salvato", "Meta salvato con successo.")



class AtlasGraphicsView(GridGraphicsView, ShiftDragRectSelectMixin):
    def __init__(self):
        super().__init__()
        self.selection_rect_item: QGraphicsRectItem = None
        self.last_selection_rect: QRectF = QRectF()
        self.selected_coords = set()
        self.alt_drag_active = False
        self.drag_start_pos = None
        self.drag_start_scene_pos = None
        self.drag_preview_item = None
        self._drag_origin_x = 0
        self._drag_origin_y = 0
        self._drag_offset_tiles = (0, 0)


    def mousePressEvent(self, event):
        if self.grid_visible and self.handle_shift_press(event, self.scene(), self.pixmap_item):
            return

        if self.grid_visible and event.modifiers() == Qt.AltModifier and self.selected_coords:

            self.alt_drag_active = True
            scene_pos = self.mapToScene(event.pos())

            coords = list(self.selected_coords)
            min_x = min(x for x, _ in coords)
            min_y = min(y for _, y in coords)
            max_x = max(x for x, _ in coords)
            max_y = max(y for _, y in coords)

            selection_rect = QRectF(
                min_x * self.tile_size,
                min_y * self.tile_size,
                (max_x - min_x + 1) * self.tile_size,
                (max_y - min_y + 1) * self.tile_size
            )

            if selection_rect.contains(scene_pos):
                self.alt_drag_active = True
                self.drag_start_pos = event.pos()
                self.drag_start_scene_pos = scene_pos
                self._drag_origin_x = min_x * self.tile_size
                self._drag_origin_y = min_y * self.tile_size
                self._create_drag_preview()
                return
            
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if self.grid_visible and self.alt_drag_active and self.drag_preview_item:
            if self.drag_start_pos is None:
                return

            # Delta del movimento in pixel (coordinate viewport → scene)
            current_pos = self.mapToScene(event.pos())
            delta_scene = current_pos - self.drag_start_scene_pos

            # Snap alla griglia
            tile_size = self.tile_size
            dx = round(delta_scene.x() / tile_size) * tile_size
            dy = round(delta_scene.y() / tile_size) * tile_size

            # Aggiorna posizione preview
            preview_x = self._drag_origin_x + dx
            preview_y = self._drag_origin_y + dy
            self.drag_preview_item.setPos(preview_x, preview_y)

            # Salva offset in tile per lo spostamento finale
            self._drag_offset_tiles = (dx // tile_size, dy // tile_size)
            return

        self.handle_shift_move(event)
        super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        
        if self.alt_drag_active:
            self.alt_drag_active = False
            self.setCursor(Qt.ArrowCursor)

            if self.drag_preview_item:
                self.scene().removeItem(self.drag_preview_item)
                self.drag_preview_item = None

            dx, dy = self._drag_offset_tiles
            if dx != 0 or dy != 0:
                target_x = min(x for x, _ in self.selected_coords) + dx
                target_y = min(y for _, y in self.selected_coords) + dy
                self._move_selected_tiles_to(target_x, target_y)

            self._drag_offset_tiles = (0, 0)
            return

        self.handle_shift_release(event, self.scene(), self.select_tiles_in_rect)
        super().mouseReleaseEvent(event)


    def _move_selected_tiles_to(self, target_tile_x: int, target_tile_y: int):
        if not self.pixmap_item or not self.selected_coords:
            return

        tile_size = self.tile_size
        source = self.pixmap_item.pixmap()
        image = source.toImage()

        # Bounding box della selezione corrente
        min_x = min(x for x, _ in self.selected_coords)
        min_y = min(y for _, y in self.selected_coords)
        width = max(x for x, _ in self.selected_coords) - min_x + 1
        height = max(y for _, y in self.selected_coords) - min_y + 1

        # Calcolo offset reale
        offset_x = target_tile_x - min_x
        offset_y = target_tile_y - min_y

        # Salva stato prima dello spostamento
        if hasattr(self.window(), "undo_stack"):
            save_state(
                self.pixmap_item,
                self.selected_coords,
                self.window().undo_stack,
                self.window().redo_stack
            )

        # Crea nuova immagine con i tile spostati
        new_image = image.copy()

        new_selected = set()

        for x, y in self.selected_coords:
            px = x * tile_size
            py = y * tile_size
            tile = image.copy(px, py, tile_size, tile_size)

            new_x = x + offset_x
            new_y = y + offset_y

            dest_x = new_x * tile_size
            dest_y = new_y * tile_size

            # Pulisce tile vecchio
            color1 = QColor(200, 200, 200)
            color2 = QColor(255, 255, 255)
            for dx in range(tile_size):
                for dy in range(tile_size):
                    checker_color = color1 if ((x + dx // tile_size) + (y + dy // tile_size)) % 2 == 0 else color2
                    new_image.setPixelColor(px + dx, py + dy, checker_color)

            # Copia tile nuovo
            for dx in range(tile_size):
                for dy in range(tile_size):
                    color = tile.pixelColor(dx, dy)
                    new_image.setPixelColor(dest_x + dx, dest_y + dy, color)

            new_selected.add((new_x, new_y))

        # Applica nuova immagine
        self.pixmap_item.setPixmap(QPixmap.fromImage(new_image))

        # Pulisce selezione vecchia visiva
        for coord in list(self.selected_coords):
            self._remove_tile_marker(coord)

        self.selected_coords.clear()

        # Aggiorna selezione a nuovi tile
        self.selected_coords = new_selected
        for coord in self.selected_coords:
            self._highlight_tile(coord)

        self.viewport().update()

    def _create_drag_preview(self):
        tile_size = self.tile_size
        coords = sorted(self.selected_coords)

        min_x = min(x for x, _ in coords)
        min_y = min(y for _, y in coords)
        max_x = max(x for x, _ in coords)
        max_y = max(y for _, y in coords)

        width = (max_x - min_x + 1) * tile_size
        height = (max_y - min_y + 1) * tile_size

        # Crea l'immagine preview
        preview = QPixmap(width, height)
        preview.fill(Qt.transparent)

        painter = QPainter(preview)
        for x, y in coords:
            src_x = x * tile_size
            src_y = y * tile_size
            tile = self.pixmap_item.pixmap().copy(src_x, src_y, tile_size, tile_size)
            dest_x = (x - min_x) * tile_size
            dest_y = (y - min_y) * tile_size
            painter.drawPixmap(dest_x, dest_y, tile)
        painter.end()

        self.drag_preview_item = self.scene().addPixmap(preview)
        self.drag_preview_item.setZValue(10)

        # salviamo la posizione iniziale dei tile selezionati
        self.drag_preview_item.setPos(self._drag_origin_x, self._drag_origin_y)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D:
            self.erase_selected_tiles()
        else:
            super().keyPressEvent(event)


    def select_tiles_in_rect(self, rect: QRectF):
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
        
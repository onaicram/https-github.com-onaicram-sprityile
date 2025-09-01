from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QShortcut
from PyQt5.QtGui import QPainter, QColor, QPixmap, QPen, QImage, QKeySequence
from PyQt5.QtCore import pyqtSignal, Qt, QRectF

from utils.controls_utils import apply_zoom, save_pixmap_dialog
from utils.states_utils import save_state
from utils.graphics_utils import create_pixel_preview, is_checker_color

class WorkView(QGraphicsView):

    mode_changed = pyqtSignal(str)
    color_picked = pyqtSignal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor(220, 220, 220))
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.NoDrag)
        
        self._current_mode = "select"
        self.pixmap_item = None
        self.checker_item = None

        delete_shortcut = QShortcut(QKeySequence("L"), self)
        delete_shortcut.activated.connect(self._handle_tile_delete)

        ruler_shortcut = QShortcut(QKeySequence("R"), self)
        ruler_shortcut.activated.connect(self._toggle_ruler)

        # Ruler Data
        self._ruler_start = None
        self._ruler_line_item = None

        # Grid Data
        self.grid_items = []
        self.grid_visible = False

        # Tile Data
        self.tile_size = 16
        self.selected_tiles = set()
        self.tile_markers = {}

        # Pixel Data
        self.selected_pixels = set()
        self.selection_overlay_items = []

        # Panning
        self._ctrl_panning = False
        self._ctrl_pan_start_scene= None

        # Shift Selection
        self._shift_rect_selecting = False
        self._shift_rect_start_scene = None
        self.selection_rect_item = None

        # Drawing/Deleting
        self._drawing = False
        self._draw_started = False
        self._deleting = False
        self._delete_started = False

        # Alt Dragging
        self._alt_drag_active = False
        self._alt_drag_start_pos = None
        self._alt_drag_start_scene = None
        self._alt_drag_preview_item = None
        self._alt_drag_origin = (0, 0)
        self._alt_drag_offset = (0, 0)

        # Current Color
        self.current_color = QColor(0, 0, 0)

    def set_mode(self, mode: str):
        self._current_mode = mode
        self.mode_changed.emit(mode)

    def set_grid_visible(self, visible: bool):
        self.grid_visible = visible

    def set_pixmap_item(self, pixmap_item):
        self.pixmap_item = pixmap_item
        
    def set_tile_size(self, tile_size: int):
        self.tile_size = tile_size


    # CONTROLS

    def wheelEvent(self, event):
        apply_zoom(self, event, zoom_in=1.15)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_G:
            main_window = self.window()
            if hasattr(main_window, "grid_box"):
                grid_box = main_window.grid_box
                grid_box.grid_button.setChecked(not grid_box.grid_button.isChecked())
                grid_box.toggle_grid()
        elif event.key() == Qt.Key_O:
            self._current_mode = "picker"
            self.mode_changed.emit("picker")
        elif event.key() == Qt.Key_P:
            new_mode = "select" if self._current_mode == "draw" else "draw"
            self._current_mode = new_mode
            self.mode_changed.emit(new_mode)
        elif event.key() == Qt.Key_Escape:
            self._current_mode = "select"
            self.mode_changed.emit("select")
        elif event.key() == Qt.Key_L:
            self._current_mode = "delete" if self._current_mode != "delete" else "select"
            self.mode_changed.emit(self._current_mode)
        else:
            self._current_mode = "select"
            self.mode_changed.emit("select")
            super().keyPressEvent(event)

    def _toggle_ruler(self):
        if self._current_mode == "ruler":
            self._current_mode = "select"
        else:
            self._current_mode = "ruler"
        self.mode_changed.emit(self._current_mode)
        self._clear_ruler()


    def _handle_tile_delete(self):  
        if self.grid_visible and self.selected_tiles:
            self._erase_selected_tiles()

    def mousePressEvent(self, event):

        # RULER MODE
        if self._current_mode == "ruler":
            self._start_ruler(event)
            return

        # CTRL + CLICK -> PAN VIEW
        if event.modifiers() & Qt.ControlModifier:
            self._start_ctrl_drag(event)
            return
        
        # SHIFT + CLICK -> RECT SELECTION
        if event.modifiers() & Qt.ShiftModifier:
            self._start_shift_rect_selection(event)
            return
        
        # ALT + CLICK -> DRAG PIXELS OR TILES
        if event.modifiers() == Qt.AltModifier:
            if self._current_mode == "select":
                self._start_alt_drag(event)
                return

        # COLOR PICKING
        if self._current_mode == "picker":
            self._handle_color_pick(event)
            return

        # DRAW PIXELS
        if self._current_mode == "draw":
            self._start_pixel_draw(event)
            return

        # DELETE PIXELS
        if self._current_mode == "delete":
            self._start_pixel_delete(event)
            return
        
        # MAIN CLICK -> SELECT/DESELECT PIXELS OR TILES
        if event.button() == Qt.LeftButton:
            self._handle_main_click_selection(event)
        
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):

        # RULER MODE - DRAW MEASUREMENT
        if self._current_mode == "ruler" and self._ruler_start:
            self._update_ruler(event)
            return

        # PIXEL AND TILE COORDINATES
        if self.pixmap_item:
            scene_pos = self.mapToScene(event.pos())
            x = int(scene_pos.x())
            y = int(scene_pos.y())
            tile_x = x // self.tile_size
            tile_y = y // self.tile_size
            self.window().update_coordinates(x, y, tile_x, tile_y)

        # CTRL + CLICK -> DRAG PAN
        if self._ctrl_panning:
            self._update_ctrl_drag(event)
            return
        
        # SHIFT + CLICK -> DRAG RECT SELECTION
        if self._shift_rect_selecting and self.selection_rect_item:
            self._update_shift_rect_selection(event)
            return

        # ALT + CLICK -> DRAG SELECTED PIXELS OR TILES
        if self._alt_drag_active and self._alt_drag_preview_item:
            self._update_alt_drag(event)
            return

        # DRAG DRAW PIXELS 
        if self._current_mode == "draw" and self._drawing:
            self._draw_pixel_at(event)
            return
        
        # DRAG DELETE PIXELS
        if self._current_mode == "delete" and self._deleting:
            self._delete_pixel_at(event)
            return

        super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):

        if self._current_mode == "ruler":
            self._end_ruler(event)
            return
         
        # CTRL + CLICK -> END PAN
        if self._ctrl_panning and event.button() == Qt.LeftButton:
            self._end_ctrl_drag()
            
        # SHIFT + CLICK -> END RECT SELECTION
        if self._shift_rect_selecting:
            self._end_shift_rect_selection()

        # ALT + CLICK -> END DRAG SELECTED PIXELS OR TILES
        if self._alt_drag_active:
            self._end_alt_drag()
            
        # DRAW PIXELS END
        if self._drawing:
            self._end_pixel_draw()
            
        # DELETE PIXELS END
        if self._deleting:
            self._end_pixel_delete()

        if self._current_mode in ("draw", "delete") and event.button() == Qt.LeftButton:
            self._save_state()
           
        super().mouseReleaseEvent(event)


    # RULER MODE
    def _start_ruler(self, event):
        scene_pos = self.mapToScene(event.pos())
        self._ruler_start = scene_pos
        #self._clear_ruler()

    def _update_ruler(self, event):
        scene_pos = self.mapToScene(event.pos())
        x0, y0 = self._ruler_start.x(), self._ruler_start.y()
        x1, y1 = scene_pos.x(), scene_pos.y()

        # Linea
        if self._ruler_line_item:
            self.scene.removeItem(self._ruler_line_item)
        self._ruler_line_item = self.scene.addLine(x0, y0, x1, y1, QPen(QColor(180, 0, 0, 160), 0.3, Qt.DotLine))
        self._ruler_line_item.setZValue(1000)

        # Etichetta
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        label = f"Δx: {int(dx)}  Δy: {int(dy)}"

        self.window().update_coordinates(int(x1), int(y1), int(x1)//self.tile_size, int(y1)//self.tile_size, label)

    def _end_ruler(self, event):
        self._ruler_start = None


    # CTRL + CLICK -> PAN VIEW
    def _start_ctrl_drag(self, event):
        if not self.pixmap_item:
            return
        self._ctrl_panning = True
        self._ctrl_pan_start_scene = event.pos()
        self.setCursor(Qt.ClosedHandCursor)

    def _update_ctrl_drag(self, event):
        if not self._ctrl_pan_start_scene:
            return

        delta = event.pos() - self._ctrl_pan_start_scene
        self._ctrl_pan_start_scene = event.pos()

        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

    def _end_ctrl_drag(self):
        self._ctrl_panning = False
        self._ctrl_pan_start_scene = None
        self.setCursor(Qt.ArrowCursor)


    # SHIFT + CLICK -> RECT SELECTION
    def _start_shift_rect_selection(self, event):
        if not self.pixmap_item:
            return

        self._shift_rect_selecting = True
        self._shift_rect_start_scene = self.mapToScene(event.pos())

        if self.selection_rect_item:
            self.scene.removeItem(self.selection_rect_item)

        self.selection_rect_item = self.scene.addRect(QRectF())
        self.selection_rect_item.setBrush(QColor(255, 165, 0, 60))  # Arancione trasparente
        self.selection_rect_item.setPen(QPen(Qt.NoPen))
        self.selection_rect_item.setZValue(10)

    def _update_shift_rect_selection(self, event):
        if not self._shift_rect_start_scene or not self.selection_rect_item:
            return
        
        current_scene_pos = self.mapToScene(event.pos())
        rect = QRectF(self._shift_rect_start_scene, current_scene_pos).normalized()
        self.selection_rect_item.setRect(rect)

    def _end_shift_rect_selection(self):

        self._deleting = False
        self._delete_started = False
        self._drawing = False
        self._draw_started = False
        
        if not self.pixmap_item or not self.selection_rect_item:
            self._shift_drag_selecting = False
            return

        rect = self.selection_rect_item.rect()
        self.scene.removeItem(self.selection_rect_item)
        self.selection_rect_item = None
        self._shift_drag_selecting = False

        image = self.pixmap_item.pixmap().toImage()

        # RECT SELECTION
        if self.grid_visible:
            tile_w = self.tile_size
            tile_h = self.tile_size
            x1 = int(rect.left() // tile_w)
            y1 = int(rect.top() // tile_h)
            x2 = int(rect.right() // tile_w)
            y2 = int(rect.bottom() // tile_h)


            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    coord = (x, y)
                    img_rect = self.pixmap_item.pixmap().rect()
                    tile_rect = QRectF(x1 * self.tile_size, y1 * self.tile_size, self.tile_size, self.tile_size)
                    if not img_rect.contains(tile_rect.toRect().topLeft()):
                        return
                    if coord not in self.selected_tiles:
                        self.selected_tiles.add(coord)
                        self._highlight_tile(coord)
                    else:
                        self.selected_tiles.remove(coord)
                        self._remove_tile_marker(coord)

            self._save_state()

        # PIXEL SELECTION
        else:
            x1 = int(rect.left())
            y1 = int(rect.top())
            x2 = int(rect.right())
            y2 = int(rect.bottom())

            # Salva prima dello stato se cambia qualcosa
            has_new = any(
                (x, y) in self.selected_pixels
                for x in range(x1, x2 + 1)
                for y in range(y1, y2 + 1)
            )

            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    if image.pixelColor(x, y).alpha() == 0:
                        continue
                    coord = (x, y)
                    if has_new:
                        self.selected_pixels.discard(coord)
                    else:
                        self.selected_pixels.add(coord)

            self._save_state()
            
            self._update_selection_overlay()


    # ALT + CLICK -> DRAG SELECTED PIXELS OR TILES
    def _start_alt_drag(self, event):
        if self.grid_visible and self.selected_tiles:
            self._start_tile_alt_drag(event)
        elif self.selected_pixels:
            self._start_pixel_alt_drag(event)

    def _update_alt_drag(self, event):
        if self.grid_visible and self.selected_tiles:
            self._update_tile_alt_drag(event)
        elif self.selected_pixels:
            self._update_pixel_alt_drag(event)

    def _end_alt_drag(self):
        if self.grid_visible and self.selected_tiles:
            self._end_tile_alt_drag()
        elif self.selected_pixels:
            self._end_pixel_alt_drag()

    def _start_pixel_alt_drag(self, event):
        pos = self.mapToScene(event.pos())
        image = self.pixmap_item.pixmap().toImage()

        x, y = int(pos.x()), int(pos.y())
        if not (0 <= x < image.width() and 0 <= y < image.height()):
            return

        if image.pixelColor(x, y).alpha() == 0:
            return

        # Calcola bounding box dei pixel selezionati
        min_x = min(px for px, _ in self.selected_pixels)
        min_y = min(py for _, py in self.selected_pixels)
        max_x = max(px for px, _ in self.selected_pixels)
        max_y = max(py for _, py in self.selected_pixels)

        rect = QRectF(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)

        if not rect.contains(pos):
            return

        self._alt_drag_active = True
        self._alt_drag_start_scene = pos
        self._alt_drag_origin = (min_x, min_y)
        
        preview = create_pixel_preview(self.pixmap_item.pixmap(), self.selected_pixels)
        self._alt_drag_preview_item = self.scene.addPixmap(preview)
        self._alt_drag_preview_item.setZValue(20)
        self._alt_drag_preview_item.setPos(min_x, min_y)

        self.setCursor(Qt.ClosedHandCursor)

    def _update_pixel_alt_drag(self, event):
        current_pos = self.mapToScene(event.pos())
        delta = current_pos - self._alt_drag_start_scene
        dx = int(round(delta.x()))
        dy = int(round(delta.y()))
        self._alt_drag_preview_item.setPos(self._alt_drag_origin[0] + dx, self._alt_drag_origin[1] + dy)
        self._alt_drag_offset = (dx, dy)

    def _end_pixel_alt_drag(self):

        if self._alt_drag_active:
            self._alt_drag_active = False
            self.setCursor(Qt.ArrowCursor)

            if self._alt_drag_preview_item:
                self.scene.removeItem(self._alt_drag_preview_item)
                self._alt_drag_preview_item = None

            dx, dy = self._alt_drag_offset

            if dx != 0 or dy != 0:

                # Applica lo spostamento dei pixel selezionati
                self._apply_pixel_move(dx, dy)

                # Salva stato
                self._save_state()

            self._alt_drag_offset = (0, 0)
            self.restore_selection(self.selected_pixels, mode="pixel")

    def _apply_pixel_move(self, dx: int, dy: int):
        if not self.pixmap_item or not self.selected_pixels:
            return
        
        pixmap = self.pixmap_item.pixmap()
        image = pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
        width = image.width()
        height = image.height()

        # Crea una copia dei pixel selezionati e dei loro colori
        moved_pixels = []
        for x, y in sorted(self.selected_pixels):
            if 0 <= x < width and 0 <= y < height:
                color = image.pixelColor(x, y)
                if color.alpha() == 0:
                     continue
                moved_pixels.append(((x + dx, y + dy), color))

        # Rendi trasparenti i pixel originali
        for x, y in self.selected_pixels:
            if 0 <= x < width and 0 <= y < height:
                image.setPixelColor(x, y, QColor(0, 0, 0, 0))

        # Applica i nuovi pixel
        for (new_x, new_y), color in moved_pixels:
            if 0 <= new_x < width and 0 <= new_y < height:
                image.setPixelColor(new_x, new_y, color)
                
        # Aggiorna pixmap e scena
        self.pixmap_item.setPixmap(QPixmap.fromImage(image))

        # Aggiorna le coordinate dei pixel selezionati
        self.selected_pixels = {(x + dx, y + dy) for (x, y) in self.selected_pixels}
        self._update_selection_overlay()

    def _create_drag_preview(self):
        preview = create_pixel_preview(self.pixmap_item.pixmap(), self.selected_pixels)
        self.drag_preview_item = self.scene.addPixmap(preview)
        self.drag_preview_item.setZValue(20)
        min_x = min(x for x, _ in self.selected_pixels)
        min_y = min(y for _, y in self.selected_pixels)
        self.drag_preview_item.setPos(min_x, min_y)

    def _start_tile_alt_drag(self, event):

        scene_pos = self.mapToScene(event.pos())
        tiles = list(self.selected_tiles)

        min_x = min(x for x, _ in tiles)
        min_y = min(y for _, y in tiles)
        max_x = max(x for x, _ in tiles)
        max_y = max(y for _, y in tiles)

        selection_rect = QRectF(
            min_x * self.tile_size,
            min_y * self.tile_size,
            (max_x - min_x + 1) * self.tile_size,
            (max_y - min_y + 1) * self.tile_size
        )

        if selection_rect.contains(scene_pos):
            self._alt_drag_active = True
            self._alt_drag_start_pos = scene_pos
            self._alt_drag_start_scene = event.pos()
            self._alt_drag_origin = (min_x * self.tile_size, min_y * self.tile_size)
            self._create_alt_drag_preview()
            return

    def _update_tile_alt_drag(self, event):
        if self._alt_drag_active and self._alt_drag_preview_item:

            if self._alt_drag_start_scene is None:
                return
            
            current_scene_pos = self.mapToScene(event.pos())
            delta_scene = current_scene_pos - self._alt_drag_start_pos

            dx = round(delta_scene.x() / self.tile_size) * self.tile_size
            dy = round(delta_scene.y() / self.tile_size) * self.tile_size

            self._alt_drag_preview_item.setPos(
                self._alt_drag_origin[0] + dx,
                self._alt_drag_origin[1] + dy
            )

            self._alt_drag_offset = (dx // self.tile_size, dy // self.tile_size)
            return

    def _end_tile_alt_drag(self):
        if self._alt_drag_active:
            self._alt_drag_active = False

            if self._alt_drag_preview_item:
                self.scene.removeItem(self._alt_drag_preview_item)
                self._alt_drag_preview_item = None

            dx, dy = self._alt_drag_offset
            if dx != 0 or dy != 0:
                target_x = min(x for x, _ in self.selected_tiles) + dx
                target_y = min(y for _, y in self.selected_tiles) + dy
                self._move_selected_tiles_by(target_x, target_y)

            self._alt_drag_offset = (0, 0)
            return

    def _create_alt_drag_preview(self):
        tile_size = self.tile_size
        tiles = sorted(self.selected_tiles)

        min_x = min(x for x, _ in tiles)
        min_y = min(y for _, y in tiles)
        max_x = max(x for x, _ in tiles)
        max_y = max(y for _, y in tiles)

        width = (max_x - min_x + 1) * tile_size
        height = (max_y - min_y + 1) * tile_size

        # Crea l'immagine preview
        preview = QPixmap(width, height)
        preview.fill(Qt.transparent)

        painter = QPainter(preview)
        for x, y in tiles:
            src_x = x * tile_size
            src_y = y * tile_size
            tile = self.pixmap_item.pixmap().copy(src_x, src_y, tile_size, tile_size)
            dest_x = (x - min_x) * tile_size
            dest_y = (y - min_y) * tile_size
            painter.drawPixmap(dest_x, dest_y, tile)
        painter.end()

        self._alt_drag_preview_item = self.scene.addPixmap(preview)
        self._alt_drag_preview_item.setZValue(10)

        # salviamo la posizione iniziale dei tile selezionati
        self._alt_drag_preview_item.setPos(min_x * tile_size, min_y * tile_size)

    def _move_selected_tiles_by(self, dx, dy):
        tile_size = self.tile_size
        source = self.pixmap_item.pixmap()
        image = source.toImage()

        # Bounding box della selezione corrente
        min_x = min(x for x, _ in self.selected_tiles)
        min_y = min(y for _, y in self.selected_tiles)

        # Calcolo offset reale
        offset_x = dx - min_x
        offset_y = dy - min_y

        self._save_state()

        # Crea nuova immagine con i tile spostati
        new_image = image.copy()

        new_selected = set()

        for x, y in self.selected_tiles:
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
        for tile in list(self.selected_tiles):
            self._remove_tile_marker(tile)

        self.selected_tiles.clear()

        # Aggiorna selezione a nuovi tile
        self.selected_tiles = new_selected
        for tile in self.selected_tiles:
            self._highlight_tile(tile)

        self.viewport().update()


    # CLICK -> SELECT/DESELECT PIXELS OR TILES
    def _handle_main_click_selection(self, event):
        if event.button() != Qt.LeftButton or not self.pixmap_item:
            return False

        pos = self.mapToScene(event.pos())
        if not self._is_pos_inside_image(pos):
            return False

        if self.grid_visible:
            self._handle_tile_click_selection(pos)
        else:
            self._handle_pixel_click_selection(pos)

        return True

    def _handle_tile_click_selection(self, pos):
        tile_x = int(pos.x() // self.tile_size)
        tile_y = int(pos.y() // self.tile_size)
        coord = (tile_x, tile_y)

        was_added = coord not in self.selected_tiles

        if was_added:
            self.selected_tiles.add(coord)
            self._highlight_tile(coord)
        else:
            self.selected_tiles.remove(coord)
            self._remove_tile_marker(coord)

        self._save_state()

        print(f"[TILE CLICK] Stato salvato. Tiles selezionati: {self.selected_tiles}")
        print(f"[TILE CLICK] Coordinate click: {pos}, tile coord: {coord}, was_added: {was_added}")
        
    def _handle_pixel_click_selection(self,pos):
        if not self.pixmap_item:
            return

        x = int(pos.x())
        y = int(pos.y())

        image = self.pixmap_item.pixmap().toImage()
        if not (0 <= x < image.width() and 0 <= y < image.height()):
            return

        alpha = image.pixelColor(x, y).alpha()
        if alpha == 0:
            return  
        
        coord = (x, y)
        was_added = coord in self.selected_pixels

        if was_added:
            self.selected_pixels.discard(coord)
        else:
            self.selected_pixels.add(coord)        
            self._save_state()
            
        self._update_selection_overlay()

    def _highlight_tile(self, coord):
        x, y = coord
        rect = QRectF(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)

        item = self.scene.addRect(rect, QPen(Qt.NoPen), QColor(255, 165, 0, 150))
        item.setZValue(9) 

        self.tile_markers[coord] = item

    def _remove_tile_marker(self, coord):
        if coord in self.tile_markers:
            self.scene.removeItem(self.tile_markers[coord])
            del self.tile_markers[coord]


    # PIXEL DRAWING
    def _start_pixel_draw(self, event):
        self._drawing = True
        self._draw_started = False
        self._draw_pixel_at(event)

    def _draw_pixel_at(self, event):
        if not self.pixmap_item:
            return

        pos = self.mapToScene(event.pos())
        x, y = int(pos.x()), int(pos.y())

        image = self.pixmap_item.pixmap().toImage()
        if not (0 <= x < image.width() and 0 <= y < image.height()):
            return

        image.setPixelColor(x, y, self.current_color)
        new_pixmap = QPixmap.fromImage(image)
        self.pixmap_item.setPixmap(new_pixmap)

    def _end_pixel_draw(self):
        self._drawing = False
        self._draw_started = False

   
    # PIXEL OR TILES DELETION
    def _start_pixel_delete(self, event):
        self._deleting = True
        self._delete_started = False
        self._delete_pixel_at(event)

    def _delete_pixel_at(self, event):
        if not self.pixmap_item:
            return

        pos = self.mapToScene(event.pos())
        x, y = int(pos.x()), int(pos.y())

        image = self.pixmap_item.pixmap().toImage()
        if not (0 <= x < image.width() and 0 <= y < image.height()):
            return

        image.setPixelColor(x, y, QColor(0, 0, 0, 0))  # trasparente
        self.pixmap_item.setPixmap(QPixmap.fromImage(image))
        self._update_selection_overlay()

    def _end_pixel_delete(self):
        self._deleting = False
        self._delete_started = False

    def _erase_selected_tiles(self):
            if not self.pixmap_item:
                return
            if not self.selected_tiles:
                return
            
            self._save_state()

            # Cancella pixel selezionati
            original = self.pixmap_item.pixmap()
            image = original.toImage()
            for x, y in self.selected_tiles:
                px, py = x * self.tile_size, y * self.tile_size
                for dx in range(self.tile_size):
                    for dy in range(self.tile_size):
                        image.setPixelColor(px + dx, py + dy, Qt.transparent)
            new_pixmap = QPixmap.fromImage(image)
            self.pixmap_item.setPixmap(new_pixmap)

            # Rimuove i marker visivi (rettangoli arancioni)
            for tile in list(self.selected_tiles):  # fai una copia per sicurezza
                self._remove_tile_marker(tile)

            # Svuota selezione logica
            self.selected_tiles.clear()

            # Rimuove eventuale rettangolo di selezione multipla
            if getattr(self, "selection_rect_item", None):
                self.scene().removeItem(self.selection_rect_item)
                self.selection_rect_item = None

            self.selected_tiles.clear()
            self._save_state()


    # COLOR PICKING
    def _handle_color_pick(self, event):
        pos = self.mapToScene(event.pos())
        x, y = int(pos.x()), int(pos.y())

        if not self._is_pos_inside_image(pos):
            return
        
        image = self.pixmap_item.pixmap().toImage()
        color = image.pixelColor(x, y)
        if color.alpha() == 0:
            return
        
        self.current_color = color
        self.color_picked.emit(color)
        self.mode_changed.emit("select")
        self._current_mode = "select"
        self.setCursor(Qt.ArrowCursor)
    

    # UTILITY METHODS
    def _is_pos_inside_image(self, pos):
        return self.pixmap_item.pixmap().rect().contains(int(pos.x()), int(pos.y()))

    def restore_tile_selection(self, coords: set):
        self.restore_selection(coords, mode="tile")

    def restore_pixel_selection(self, coords: set):
        self.restore_selection(coords, mode="pixel")

    def restore_selection(self, coords: set, mode: str = "pixel"):
        self._clear_all_selection()

        if mode == "tile":
            for coord in coords:
                self.selected_tiles.add(coord)
                self._highlight_tile(coord)
        else:
            for coord in coords:
                self.selected_pixels.add(coord)
            self._update_selection_overlay()

    def _clear_all_selection(self):
        if hasattr(self, "tile_markers"):
            for item in self.tile_markers.values():
                self.scene.removeItem(item)
            self.tile_markers.clear()
        self.selected_tiles.clear()

        for item in self.selection_overlay_items:
            self.scene.removeItem(item)
        self.selection_overlay_items.clear()
        self.selected_pixels.clear()

    def _update_selection_overlay(self):
        for item in self.selection_overlay_items:
            self.scene.removeItem(item)
        self.selection_overlay_items.clear()

        if not self.pixmap_item or not self.selected_pixels:
            return

        for x, y in self.selected_pixels:
            rect = QRectF(x, y, 1, 1)
            item = self.scene.addRect(rect, QPen(Qt.NoPen), QColor(100, 100, 100, 120))
            item.setZValue(9)
            self.selection_overlay_items.append(item)

    def _reset_interaction_flags(self):
        self._deleting = False
        self._delete_started = False
        self._drawing = False
        self._draw_started = False
        self._alt_drag_active = False
        self._alt_drag_offset = (0, 0)
        self.setCursor(Qt.ArrowCursor)

    def _save_state(self):
        # print(f"[SAVE_STATE] Pre-save selected_tiles: {self.selected_tiles}")
        save_state(
            self.pixmap_item,
            self.selected_pixels if not self.grid_visible else self.selected_tiles,
            self.window().undo_stack,
            self.window().redo_stack
        )

    def export_selection(self):
        if not self.grid_visible or not self.pixmap_item or not self.selected_tiles:
            print("[DEBUG] Nessuna griglia visibile o nessuna selezione tile")
            return

        tile_size = self.tile_size
        source_pixmap = self.pixmap_item.pixmap()
        selected_tiles = set(self.selected_tiles)

        # Calcola bounding box
        min_x = min(x for x, _ in selected_tiles)
        min_y = min(y for _, y in selected_tiles)
        max_x = max(x for x, _ in selected_tiles)
        max_y = max(y for _, y in selected_tiles)

        width = (max_x - min_x + 1) * tile_size
        height = (max_y - min_y + 1) * tile_size

        final_pixmap = QPixmap(width, height)
        final_pixmap.fill(Qt.transparent)

        painter = QPainter(final_pixmap)
        source_image = source_pixmap.toImage()

        for x, y in selected_tiles:
            src_x = x * tile_size
            src_y = y * tile_size

            tile_image = QImage(tile_size, tile_size, QImage.Format_ARGB32)
            tile_image.fill(Qt.transparent)

            for i in range(tile_size):
                for j in range(tile_size):
                    px = src_x + i
                    py = src_y + j
                    if px < source_image.width() and py < source_image.height():
                        color = source_image.pixelColor(px, py)
                        
                        if not is_checker_color(color):
                            tile_image.setPixelColor(i, j, color)

            dest_x = (x - min_x) * tile_size
            dest_y = (y - min_y) * tile_size
            painter.drawPixmap(dest_x, dest_y, QPixmap.fromImage(tile_image))

        painter.end()

        save_pixmap_dialog(self.window(), QPixmap(final_pixmap))


    def remove_color(self):
        if not self.pixmap_item:
            return

        image = self.pixmap_item.pixmap().toImage()
        for y in range(image.height()):
            for x in range(image.width()):
                if image.pixelColor(x, y) == self.current_color:
                    image.setPixelColor(x, y, QColor(0, 0, 0, 0))
        self.pixmap_item.setPixmap(QPixmap.fromImage(image))
        
    def _update_tile_selection_visuals(self):
        self._clear_all_tile_highlights()
        for coord in self.selected_tiles:
            self._highlight_tile(coord)

    def _clear_all_tile_highlights(self):
        if hasattr(self, "tile_markers"):
            for item in self.tile_markers.values():
                self.scene.removeItem(item)
            self.tile_markers.clear()

    def _clear_ruler(self):
        if self._ruler_line_item:
            self.scene.removeItem(self._ruler_line_item)
            self._ruler_line_item = None
        self._ruler_start = None


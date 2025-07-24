import sys
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QColorDialog,
    QMainWindow, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage, QPen
from PyQt5.QtCore import Qt, pyqtSignal, QRectF

from tile_splitter.tile_splitter import TileSplitterWindow
from atlas.atlas_manager import AtlasManagerWindow
from utils.graphics_utils import load_image_with_checker
from utils.controls_utils import save_pixmap_dialog, apply_zoom, CtrlDragMixin, is_atlas_file, create_pixel_preview, ClickableLabel
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

        self.selected_pixels = set()
        self.drag_selecting = False
        self.alt_drag_active = False
        self.selection_rect_item = None
        self.drag_preview_item = None
        self._drag_origin = (0, 0)
        self._drag_offset = (0, 0)
        self.selection_overlay_item = None

        self._current_mode = "select"  # Modalità iniziale
        self.current_color = QColor(0, 0, 0)
        
        self._drawing = False
        self._draw_started = False
        self._deleting = False
        self._delete_started = False

    color_picked = pyqtSignal(str)
    mode_changed = pyqtSignal(str)

    def set_stack_refs(self, undo_stack, redo_stack):
        self._undo_stack = undo_stack
        self._redo_stack = redo_stack


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_O:
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


    def mousePressEvent(self, event):
        if self.pixmap_item is None:
            return

        pos = self.mapToScene(event.pos())
        x, y = int(pos.x()), int(pos.y())

        # Dragging con Ctrl
        if event.modifiers() & Qt.ControlModifier:
            self.handle_drag_press(event)
            super().mousePressEvent(event)
            return

        # Color Picking
        if 0 <= x < self.pixmap_item.pixmap().width() and 0 <= y < self.pixmap_item.pixmap().height():
            image = self.pixmap_item.pixmap().toImage()
            if self._current_mode == "picker":
                color = image.pixelColor(x, y)
                hex_color = color.name().upper()
                self.color_picked.emit(hex_color)
                self.current_color = color
                self._current_mode = "select"
                self.setCursor(Qt.ArrowCursor)
                return

        # Rect selezione con Shift
        if event.modifiers() & Qt.ShiftModifier:
            if self._current_mode == "select":
                self.drag_selecting = True
                self.drag_start_pos = pos

                if self.selection_rect_item:
                    self.scene.removeItem(self.selection_rect_item)
                self.selection_rect_item = self.scene.addRect(QRectF())
                self.selection_rect_item.setBrush(QColor(255, 165, 0, 60))
                self.selection_rect_item.setPen(QPen(QColor(255, 165, 0), 0))
                self.selection_rect_item.setZValue(10)
                return

        # Pixel drag con Alt
        if event.modifiers() == Qt.AltModifier and self.selected_pixels:
            if self._current_mode == "select":
                rect = QRectF(
                    min(x for x, _ in self.selected_pixels),
                    min(y for _, y in self.selected_pixels),
                    max(x for x, _ in self.selected_pixels) - min(x for x, _ in self.selected_pixels) + 1,
                    max(y for _, y in self.selected_pixels) - min(y for _, y in self.selected_pixels) + 1,
                )
                if rect.contains(pos):
                    image = self.pixmap_item.pixmap().toImage()
                    if 0 <= x < image.width() and 0 <= y < image.height():
                        if image.pixelColor(x, y).alpha() == 0:
                            return 
                    self.alt_drag_active = True
                    self.drag_start_pos = event.pos()
                    self.drag_start_scene_pos = pos
                    self._drag_origin = (rect.x(), rect.y())
                    self._create_drag_preview()
                    self.setCursor(Qt.ClosedHandCursor)
                    return

        # Disegno Pixel
        if self._current_mode == "draw":
            self._drawing = True
            self._draw_started = False 
            self.draw_pixel(x, y)
            return

        # Cancellazione Pixel
        if self._current_mode == "delete":
            self._deleting = True
            self._delete_started = False
            self.delete_pixel(x, y)
            return
        
        # Click singolo su pixel
        if event.button() == Qt.LeftButton:
            if (x, y) in self.selected_pixels:
                self.remove_pixel_from_selection(x, y)
            else:
                self.add_pixel_to_selection(x, y)

        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):

        # Rect selezione con Shift
        if self.drag_selecting and self.selection_rect_item:
            current_pos = self.mapToScene(event.pos())
            rect = QRectF(self.drag_start_pos, current_pos).normalized()
            self.selection_rect_item.setRect(rect)
            return

        # Pixel Drag con Alt
        if self.alt_drag_active and self.drag_preview_item:
            current_scene_pos = self.mapToScene(event.pos())
            delta = current_scene_pos - self.drag_start_scene_pos
            dx = int(round(delta.x()))
            dy = int(round(delta.y()))
            self.drag_preview_item.setPos(self._drag_origin[0] + dx, self._drag_origin[1] + dy)
            self._drag_offset = (dx, dy)
            return
        
        #Disegno e Cancellazione Pixel
        if event.buttons() & Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            x, y = int(pos.x()), int(pos.y())
            if self._current_mode == "delete" and self._deleting:
                if not self._delete_started:
                    save_state(self.pixmap_item, self.selected_pixels, self._undo_stack, self._redo_stack)
                    self._delete_started = True
                self.delete_pixel(x, y)
                return

            if self._current_mode == "draw" and self._drawing:
                if not self._draw_started:
                    save_state(self.pixmap_item, self.selected_pixels, self._undo_stack, self._redo_stack)
                    self._draw_started = True
                self.draw_pixel(x, y)
                return
            
        self.handle_drag_move(event)
        super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):

        # Rect selezione con Shift
        if self.drag_selecting and self.selection_rect_item:
            rect = self.selection_rect_item.rect().toRect()
            self.scene.removeItem(self.selection_rect_item)
            self.selection_rect_item = None
            self.drag_selecting = False

            image = self.pixmap_item.pixmap().toImage()
            for x in range(rect.left(), rect.right() + 1):
                for y in range(rect.top(), rect.bottom() + 1):
                    if 0 <= x < image.width() and 0 <= y < image.height():
                        alpha = image.pixelColor(x, y).alpha()
                        if alpha == 0:
                            continue
                        if (x, y) in self.selected_pixels:
                            self.remove_pixel_from_selection(x, y)
                        else:
                            self.add_pixel_to_selection(x, y)
            return

        # Pixel Drag con Alt
        if self.alt_drag_active:
            self.alt_drag_active = False
            self.setCursor(Qt.ArrowCursor)
            if self.drag_preview_item:
                self.scene.removeItem(self.drag_preview_item)
                self.drag_preview_item = None
            dx, dy = self._drag_offset
            if dx != 0 or dy != 0:
                save_state(self.pixmap_item, self.selected_pixels, self._undo_stack, self._redo_stack)
                self.apply_pixel_move(dx, dy)
            self._drag_offset = (0, 0)
            return
        
        if self._drawing:
            self._drawing = False
            self._draw_started = False

        if self._deleting:
            self._deleting = False
            self._delete_started = False

        if self._current_mode in ("draw", "delete") and event.button() == Qt.LeftButton:
            save_state(self.pixmap_item, self.selected_pixels, self._undo_stack, self._redo_stack)


        self.handle_drag_release(event)
        super().mouseReleaseEvent(event)

    
    def update_selection_overlay(self):
        if self.pixmap_item is None:
            return

        base = self.pixmap_item.pixmap()
        width = base.width()
        height = base.height()

        # Overlay vuoto trasparente
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        for x, y in self.selected_pixels:
            if 0 <= x < width and 0 <= y < height:
                color = QColor(200, 200, 200, 100)
                image.setPixelColor(x, y, color)

        overlay = QPixmap.fromImage(image)

        if self.selection_overlay_item:
            self.scene.removeItem(self.selection_overlay_item)

        self.selection_overlay_item = self.scene.addPixmap(overlay)
        self.selection_overlay_item.setZValue(self.pixmap_item.zValue() + 1)


    def add_pixel_to_selection(self, x, y):
        self.selected_pixels.add((x, y))
        self.update_selection_overlay()


    def draw_pixel(self, x, y):
        image = self.pixmap_item.pixmap().toImage()
        if 0 <= x < image.width() and 0 <= y < image.height():
            image.setPixelColor(x, y, self.current_color)
            new_pixmap = QPixmap.fromImage(image)
            self.pixmap_item.setPixmap(new_pixmap)

    
    def delete_pixel(self, x, y):
        image = self.pixmap_item.pixmap().toImage()
        if 0 <= x < image.width() and 0 <= y < image.height():
            image.setPixelColor(x, y, QColor(0, 0, 0, 0))  # Trasparente
            self.pixmap_item.setPixmap(QPixmap.fromImage(image))
            self.update()

    
    def apply_pixel_move(self, dx: int, dy: int):
        if not self.pixmap_item or not self.selected_pixels:
            return
        
        main_window = self.window()
        if hasattr(main_window, "save_state"):
            main_window.save_state()
        
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
        
        self.selected_pixels.clear()
        self.update_selection_overlay()
        

    def remove_pixel_from_selection(self, x, y):
        self.selected_pixels.discard((x, y))
        self.update_selection_overlay()


    def _create_drag_preview(self):
        preview = create_pixel_preview(self.pixmap_item.pixmap(), self.selected_pixels)
        self.drag_preview_item = self.scene.addPixmap(preview)
        self.drag_preview_item.setZValue(20)
        min_x = min(x for x, _ in self.selected_pixels)
        min_y = min(y for _, y in self.selected_pixels)
        self.drag_preview_item.setPos(min_x, min_y)

        
    def wheelEvent(self, event):
        apply_zoom(self, event, zoom_in=1.15)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.undo_stack = []
        self.redo_stack = []
        self.current_tile_size = 16  # Dimensione predefinita dei tasselli

        self.mode = enumerate(["select", "picker", "draw", "delete"])
        
        self.setWindowTitle("Sprityle")

        self.view = ImageViewer()
        self.view.set_stack_refs(self.undo_stack, self.redo_stack)

        self.original_pixmap = None  
        self.view.color_picked.connect(self.show_color)
        self.view.mode_changed.connect(self.update_mode_label)

        self.hotkey_label = QLabel("L - Cancella   |   O - Preleva   |   P - Disegna |   Esc - Seleziona")
        self.hotkey_label.setAlignment(Qt.AlignLeft)
        self.hotkey_label.setFixedWidth(300)
        self.mode_label = QLabel("⚪ SELEZIONE")
        self.mode_label.setAlignment(Qt.AlignRight)
        
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.hotkey_label)
        mode_layout.addWidget(self.mode_label)

        self.tile_splitter_button = QPushButton("Gestione Tile")
        self.tile_splitter_button.setFixedWidth(120)
        self.tile_splitter_button.clicked.connect(self.open_tile_splitter)

        self.atlas_manager_button = QPushButton("Gestione Atlas")
        self.atlas_manager_button.setFixedWidth(120)
        self.atlas_manager_button.clicked.connect(self.open_atlas_manager)

        self.function_layout = QHBoxLayout()
        self.function_layout.addWidget(self.tile_splitter_button)
        self.function_layout.addWidget(self.atlas_manager_button)
        self.function_layout.setAlignment(Qt.AlignCenter)

        # Color 
        self.color_label = QLabel("Colore selezionato:")
        self.color_label.setMaximumWidth(90)

        self.color_preview = ClickableLabel()
        self.color_preview.clicked.connect(self.choose_color)
        self.color_preview.setFixedSize(40, 15)
        self.color_preview.setStyleSheet(f"background-color: {self.view.current_color.name()}; border: 1px solid black;")

        self.color_field = QLineEdit("Nessun colore")
        self.color_field.setFixedWidth(100)

        self.copy_button = QPushButton("Copia colore")
        self.copy_button.setFixedWidth(100)
        self.copy_button.clicked.connect(self.copy_color)

        self.remove_color_button = QPushButton("Rimuovi colore")
        self.remove_color_button.setFixedWidth(100)
        self.remove_color_button.clicked.connect(self.remove_selected_color)

        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(self.color_field)
        color_layout.addWidget(self.copy_button)
        color_layout.addWidget(self.remove_color_button)
        color_layout.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addLayout(self.function_layout)
        layout.addLayout(mode_layout)
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
        self.reset_button.clicked.connect(self.reset)

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

    def keyPressEvent(self, event):
        if self.view:
            self.view.keyPressEvent(event)


    def update_mode_label(self, mode: str):
        mode_map = {
            "select": "⚪ SELEZIONE",
            "draw": "🟢 DISEGNO",
            "picker": "🔵 PICKER",
            "delete": "❌ CANCELLA"
        }
        self.mode_label.setText(mode_map.get(mode, "⚪ SELEZIONE"))

    def choose_color(self):
        color = QColorDialog.getColor(initial=self.view.current_color, parent=self, title="Scegli colore pennello")
        if color.isValid():
            self.view.current_color = color
            self.color_field.setText(color.name().upper())
            self.update_color_preview()

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

    
    def update_color_preview(self):
        self.color_preview.setStyleSheet(f"background-color: {self.view.current_color.name()}; border: 1px solid black;")


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
            
 
    def reset(self):
        reset_state(
            self.view.pixmap_item,
            self.original_pixmap,
            set(),
            self.undo_stack,
            self.redo_stack,
            restore_selection_fn=None,
            color_field=self.color_field,
            color_preview=self.color_preview,
            current_color=self.view.current_color,
            parent=self
        )

    def save_state(self):
        save_state(self.view.pixmap_item, self.view.selected_pixels, self.undo_stack, self.redo_stack)


    def undo(self):
        undo_state(
            self.view.pixmap_item,
            self.view.selected_pixels,
            self.undo_stack,
            self.redo_stack,
            restore_selection_fn=None
        )

    def redo(self):
        redo_state(
            self.view.pixmap_item,
            self.view.selected_pixels,
            self.undo_stack,
            self.redo_stack,
            restore_selection_fn=None
        )

    def show_color(self, hex_color):
        self.color_field.setText(hex_color)
        self.view.current_color = QColor(hex_color)
        self.update_color_preview()


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






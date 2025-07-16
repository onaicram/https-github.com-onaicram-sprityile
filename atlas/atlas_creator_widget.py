from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem, QShortcut, QLabel,QSpinBox,
    QFileDialog, QMessageBox
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QFont, QTextOption, QKeySequence
from PyQt5.QtCore import Qt

from atlas.atlas_generated_window import AtlasGeneratedWindow
from utils.controls_utils import CtrlDragMixin, is_atlas_file
from utils.meta_utils import MetaUtils


class AtlasCreatorView(QGraphicsView, CtrlDragMixin):
    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QColor(220, 220, 220))
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.image_items = []
        self.last_offset = 0
        self.item_map = {}

        self.tile_size = 96
        self.selected_pixmaps = set()

    def mouseMoveEvent(self, event):
        self.handle_drag_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.handle_drag_release(event)
        super().mouseReleaseEvent(event)

    def show_images(self, images, paths, start_idx):
        spacing = 40
        fixed_size = self.tile_size

        if not hasattr(self, "last_offset"):
            self.last_offset = 0

        x_offset = self.last_offset

        for idx, (pixmap, path) in enumerate(zip(images, paths), start=start_idx):
            name = path.split("/")[-1]
            group = {}

            # --- Riquadro base
            rect = QGraphicsRectItem(0, 0, fixed_size, fixed_size)
            rect.setBrush(QBrush(QColor(250, 250, 250)))
            rect.setPen(QPen(QColor(150, 150, 150)))
            rect.setZValue(0)

            # --- Immagine
            scaled = pixmap.scaled(fixed_size, fixed_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            img_item = QGraphicsPixmapItem(scaled)
            dx = (fixed_size - scaled.width()) / 2
            dy = (fixed_size - scaled.height()) / 2
            img_item.setOffset(dx, dy)
            img_item.setZValue(1)

            # --- Testo
            text_item = QGraphicsTextItem(name)
            text_item.setFont(QFont("Arial", 8))
            text_item.setTextWidth(self.tile_size)
            text_option = QTextOption(Qt.AlignCenter)
            text_item.document().setDefaultTextOption(text_option)
            text_item.setDefaultTextColor(Qt.darkGray)
            text_item.setPos((fixed_size - text_item.boundingRect().width()) / 2, self.tile_size + 2)
            text_item.setZValue(2)

            # --- Gruppo
            group_item = self.scene.createItemGroup([rect, img_item, text_item])
            group_item.setPos(x_offset, 0)
            group_item.setZValue(3)

            # --- Highlight selezione (invisibile di default)
            highlight = QGraphicsRectItem(0, 0, fixed_size, fixed_size)
            highlight.setBrush(QColor(255, 165, 0, 150))
            highlight.setPen(QPen(Qt.NoPen))
            highlight.setZValue(5)
            highlight.setVisible(False)
            highlight.setParentItem(group_item)

            # --- Registra tutto
            group["rect"] = rect
            group["pixmap"] = pixmap
            group["path"] = path
            group["group"] = group_item
            group["highlight"] = highlight
            
            self.image_items.append(group)

            self.item_map[rect] = group
            self.item_map[img_item] = group
            self.item_map[text_item] = group
            self.item_map[group_item] = group

            x_offset += fixed_size + spacing

        self.last_offset = x_offset


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            items = self.scene.items(scene_pos)

            for item in items:
                if item in self.item_map:
                    group = self.item_map[item]
                    pixmap = group['pixmap']
                    if pixmap in self.selected_pixmaps:
                        group['highlight'].setVisible(False)
                        self.selected_pixmaps.remove(pixmap)
                    else:
                        group['highlight'].setVisible(True)
                        self.selected_pixmaps.add(pixmap)
                    return

        self.handle_drag_press(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.handle_drag_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.handle_drag_release(event)
        super().mouseReleaseEvent(event)

    def relayout_images(self):
        spacing = 16
        fixed_size = self.tile_size
        x_offset = 0

        for group in self.image_items:
            group["group"].setPos(x_offset, 0)
            x_offset += fixed_size + spacing

        self.last_offset = x_offset


class AtlasCreator(QWidget):
    def __init__(self, edit_mode=False, atlas_name="", atlas_path=None, initial_image = None, parent=None):
        super().__init__()
        self.edit_mode = edit_mode
        self.setWindowTitle(self._get_window_title())
        self.atlas_name = atlas_name if edit_mode else ""
        self.atlas_path = atlas_path

        self.resize(600, 400)

        self.loaded_images = []
        self.loaded_names = []

        if initial_image:
            pixmap = QPixmap(initial_image)
            if not pixmap.isNull():
                self.loaded_images.append(pixmap)
                self.loaded_names.append(initial_image)

        self.view = AtlasCreatorView()
        self.init_ui() 

    def _get_window_title(self):
        if self.edit_mode:
            return f"Modifica Atlas"
        return "Crea Atlas da Immagini"
    
    def init_ui(self):

        if self.edit_mode:
            label_text = f"🟢 MODIFICA - {self.atlas_name}"
        else:
            label_text = "⚪ NUOVO"

        self.mode_label = QLabel(label_text)
        self.mode_label.setAlignment(Qt.AlignCenter)
         
        self.load_button = QPushButton()
        self.load_button.setFixedWidth(100)
        self.load_button.clicked.connect(self.load_images)

        self.delete_button = QPushButton("Elimina immagini")
        self.delete_button.setFixedWidth(100)
        self.delete_button.clicked.connect(self.delete_selected_images)

        self.toggle_all_button = QPushButton("Seleziona tutte")
        self.toggle_all_button.setCheckable(True)
        self.toggle_all_button.setFixedWidth(100)
        self.toggle_all_button.clicked.connect(self.toggle_all_images)

        self.select_all_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        self.select_all_shortcut.activated.connect(lambda: self.toggle_all_button.click())

        self.generate_atlas_button = QPushButton()
        self.generate_atlas_button.setFixedWidth(100)
        self.generate_atlas_button.clicked.connect(self.open_generate_atlas)

        if self.edit_mode:
            self.load_button.setText("Aggiungi immagini")
            self.generate_atlas_button.setText("Aggiorna Atlas")
        else:
            self.load_button.setText("Carica immagini")
            self.generate_atlas_button.setText("Genera Atlas")

        self.delete_shortcut = QShortcut(QKeySequence("D"), self)
        self.delete_shortcut.activated.connect(lambda: self.delete_button.click())

        self.tile_size_spin = QSpinBox()
        self.tile_size_spin.setRange(8, 256)
        self.tile_size_spin.setValue(16)

        self.cols_spin = QSpinBox()
        self.cols_spin.setRange(1, 64)
        self.cols_spin.setValue(60)

        self.rows_spin = QSpinBox()
        self.rows_spin.setRange(1, 64)
        self.rows_spin.setValue(20)

        # Label + layout
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel("Tile size:"))
        controls_layout.addWidget(self.tile_size_spin)
        controls_layout.addWidget(QLabel("Cols:"))
        controls_layout.addWidget(self.cols_spin)
        controls_layout.addWidget(QLabel("Rows:"))
        controls_layout.addWidget(self.rows_spin)
        controls_layout.addWidget(self.generate_atlas_button)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.load_button)
        btn_layout.addWidget(self.delete_button)
        btn_layout.addWidget(self.toggle_all_button)
        btn_layout.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.mode_label)
        layout.addWidget(self.view)
        layout.addLayout(btn_layout)   
        layout.addLayout(controls_layout)
        self.setLayout(layout)


    def load_images(self):
        pixmaps = []
        files, _ = QFileDialog.getOpenFileNames(self, "Seleziona immagini", "", "Immagini (*.png *.jpg *.jpeg *.bmp)")
        if not files:
            return
        
        for file in files:
            if file in self.loaded_names:
                QMessageBox.warning(self, "Errore", f"L'immagine '{file}' è già stata caricata.")
                continue
            if is_atlas_file(file):
                QMessageBox.warning(self, "Non consentito", f"Non è possibile caricare file atlas.\n{file}")
                continue
            pixmap = QPixmap(file)
            pixmaps.append(pixmap)

        self.load_images_from_pixmaps_and_paths(pixmaps, files)


    def delete_selected_images(self): 
        to_remove = []
        for item in self.view.image_items:
            is_visible = item["highlight"].isVisible()
            if is_visible:
                to_remove.append(item)

        for item in to_remove:
            self.view.scene.removeItem(item["group"])
            self.view.image_items.remove(item)

            if item["path"] in self.loaded_names:
                self.loaded_names.remove(item["path"])

            if item["pixmap"] in self.view.selected_pixmaps:
                self.view.selected_pixmaps.remove(item["pixmap"])

        self.view.relayout_images()


    def toggle_all_images(self):
        if self.toggle_all_button.isChecked():
            for item in self.view.image_items:
                item["highlight"].setVisible(True)
                self.view.selected_pixmaps.add(item["pixmap"])

            self.toggle_all_button.setText("Deseleziona Tutto")
        else:
            for item in self.view.image_items:
                item["highlight"].setVisible(False)
                self.view.selected_pixmaps.clear()

            self.toggle_all_button.setText("Seleziona Tutto")


    def open_generate_atlas(self):

        tile_size = self.tile_size_spin.value()
        cols = self.cols_spin.value()
        rows = self.rows_spin.value()

        if hasattr(self, 'atlas_window') and self.atlas_window:
            self.atlas_window.close()

        pixmaps = list(self.view.selected_pixmaps)

        if self.edit_mode:
            meta = MetaUtils.load_meta(self.atlas_path)
            end_tile = meta.get("end_tile", [2, 2]) if meta else [2, 2]
            self.generated_window = AtlasGeneratedWindow(
                tile_size, cols, rows, images_to_insert=pixmaps, 
                edit_mdode=True, base_atlas=self.atlas_path, 
                end_tile=end_tile
            )
        else:
            self.generated_window = AtlasGeneratedWindow(
                tile_size, cols, rows,
                images_to_insert=pixmaps,
                edit_mdode=False
            )

        self.generated_window.show()

    def load_images_from_pixmaps_and_paths(self, pixmaps, paths):

        tile_size = self.tile_size_spin.value()

        if not pixmaps or not paths or len(pixmaps) != len(paths):
            return

        new_images = []
        new_paths = []

        for pixmap, path in zip(pixmaps, paths):
            if path in self.loaded_names:
                continue
            if pixmap.isNull():
                continue
            if is_atlas_file(path):
                continue

            new_images.append(pixmap)
            new_paths.append(path)

        if not new_images:
            return

        if self.edit_mode and self.atlas_path:
            meta = MetaUtils.load_meta(self.atlas_path)
            end_tile = meta.get("end_tile", [2, 2]) 
            x_tile = end_tile[0]
            spacing = 16
            self.view.last_offset = x_tile * tile_size + spacing
        else:
            self.view.last_offset = 0

        # --- Carica immagini ---
        start_idx = len(self.loaded_images)
        self.loaded_images.extend(new_images)
        self.loaded_names.extend(new_paths)
        self.view.show_images(new_images, new_paths, start_idx)


    

        





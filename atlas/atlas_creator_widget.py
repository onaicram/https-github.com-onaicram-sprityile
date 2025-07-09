from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsView,
    QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem, QGraphicsTextItem,
    QFileDialog, QMessageBox
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QFont, QTextOption
from PyQt5.QtCore import Qt, QRectF

from utils.controls_utils import CtrlDragMixin


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
        spacing = 16
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
            text_item.setPos(0, self.tile_size + 2)
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
            highlight.setParentItem(group_item)  # ⬅️ FONDAMENTALE

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
                        print(f"Deselezionato: {group['path'].split('/')[-1]}")
                    else:
                        group['highlight'].setVisible(True)
                        self.selected_pixmaps.add(pixmap)
                        print(f"Selezionato: {group['path'].split('/')[-1]}")
                    return  # evita doppio trigger

        self.handle_drag_press(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.handle_drag_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.handle_drag_release(event)
        super().mouseReleaseEvent(event)


class AtlasCreator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crea Atlas da Immagini")
        self.resize(600, 400)

        self.loaded_images = []
        self.loaded_names = []

        self.view = AtlasCreatorView()

        self.load_button = QPushButton("Carica immagini")
        self.load_button.setFixedWidth(120)
        self.load_button.clicked.connect(self.load_images)

        self.delete_button = QPushButton("Elimina selezionate")
        self.delete_button.setFixedWidth(120)
        self.delete_button.clicked.connect(self.delete_selected_images)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.load_button)
        btn_layout.addWidget(self.delete_button)
        btn_layout.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Seleziona immagini", "", "Immagini (*.png *.jpg *.jpeg *.bmp)")
        if not files:
            return

        new_images = []
        new_paths = []

        for file_path in files:
            if file_path in self.loaded_names:
                continue

            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                QMessageBox.warning(self, "Errore", f"Immagine non valida:\n{file_path}")
            else:
                new_images.append(pixmap)
                new_paths.append(file_path)

        if not new_images:
            return

        start_idx = len(self.loaded_images)
        self.loaded_images.extend(new_images)
        self.loaded_names.extend(new_paths)
        self.view.show_images(new_images, new_paths, start_idx)

    def delete_selected_images(self):
        print("\n--- AVVIO CANCELLAZIONE ---")

        to_remove = []
        for item in self.view.image_items:
            is_visible = item["highlight"].isVisible()
            path = item["path"]
            print(f"Checking: {path}, selezionata: {is_visible}")
            if is_visible:
                to_remove.append(item)

        print(f"Totali da rimuovere: {len(to_remove)}")

        for item in to_remove:
            print(f"Rimuovo: {item['path']}")
            self.view.scene.removeItem(item["group"])
            self.view.image_items.remove(item)
            if item["path"] in self.loaded_names:
                self.loaded_names.remove(item["path"])

    

        





from PyQt5.QtWidgets import QFileDialog, QGraphicsPixmapItem, QMessageBox, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QPixmap, QColor, QPainter, QBrush
from PyQt5.QtCore import QRectF
from typing import Optional

def draw_checkerboard_for_view(view, tile_size: int):
    if view.pixmap_item is None:
        return

    # controlla se checker_item è valido
    if hasattr(view, "checker_item") and view.checker_item is not None:
        try:
            view.scene().removeItem(view.checker_item)
        except RuntimeError:
            pass  # È già stato distrutto, ignora

    pixmap = view.pixmap_item.pixmap()
    checker_pixmap = draw_checkerboard_pixmap(pixmap.width(), pixmap.height(), tile_size)
    checker_item = QGraphicsPixmapItem(checker_pixmap)
    checker_item.setZValue(0)
    view.scene().addItem(checker_item)
    view.checker_item = checker_item


def draw_checkerboard_pixmap(width, height, tile_size=16):
    checkerboard = QPixmap(width, height)
    checkerboard.fill(QColor(0, 0, 0, 0))  # Trasparente

    painter = QPainter(checkerboard)
    color1 = QColor(200, 200, 200)
    color2 = QColor(255, 255, 255)

    for y in range(0, height, tile_size):
        for x in range(0, width, tile_size):
            color = color1 if ((x // tile_size + y // tile_size) % 2 == 0) else color2
            painter.fillRect(x, y, tile_size, tile_size, color)

    painter.end()
    return checkerboard


def auto_fit_view(view, pixmap_or_pixitem, margin_ratio=0.9):

    if isinstance(pixmap_or_pixitem, QGraphicsPixmapItem):
        pixmap = pixmap_or_pixitem.pixmap()
    else:
        pixmap = pixmap_or_pixitem
        
    view_width = view.viewport().width()
    view_height = view.viewport().height()
    pixmap_width = pixmap.width()
    pixmap_height = pixmap.height()

    scale_x = view_width / pixmap_width
    scale_y = view_height / pixmap_height
    scale = min(scale_x, scale_y) * margin_ratio

    view.resetTransform()
    view.scale(scale, scale)

    if isinstance(pixmap_or_pixitem, QGraphicsPixmapItem):
        view.centerOn(pixmap_or_pixitem)
    else:
        view.centerOn(pixmap_width / 2, pixmap_height / 2)


def load_image_with_checker(view, scene, pixmap: Optional[QPixmap] = None, parent=None, tile_size=16) -> Optional[QGraphicsPixmapItem]:
    if pixmap is None:
        file_path, _ = QFileDialog.getOpenFileName(parent, "Apri immagine", "", "Immagini (*.png *.jpg *.bmp)")
        if not file_path:
            return None
        pixmap = QPixmap(file_path)

    if pixmap.isNull():
        if parent:
            QMessageBox.warning(parent, "Errore", "Immagine non valida.")
        return None

    scene.clear()

    checker = draw_checkerboard_pixmap(pixmap.width(), pixmap.height(), tile_size)
    checker_item = QGraphicsPixmapItem(checker)
    checker_item.setZValue(0)
    scene.addItem(checker_item)

    pixmap_item = QGraphicsPixmapItem(pixmap)
    pixmap_item.setZValue(1)
    scene.addItem(pixmap_item)

    view.setSceneRect(QRectF(pixmap.rect()))
    auto_fit_view(view, pixmap_item)

    return pixmap_item

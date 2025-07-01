from PyQt5.QtWidgets import QFileDialog, QGraphicsPixmapItem, QMessageBox, QGraphicsView, QGraphicsScene
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPen
from PyQt5.QtCore import QRectF
from typing import Optional


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

def draw_grid_lines(scene, pixmap_width, pixmap_height, tile_size=16, z=10, color=QColor(255, 100, 0, 255)):
    grid_items = []
    pen = QPen(color)
    pen.setWidthF(0.0)

    for x in range(0, pixmap_width + 1, tile_size):
        line = scene.addLine(x, 0, x, pixmap_height, pen)
        line.setZValue(z)
        grid_items.append(line)

    for y in range(0, pixmap_height + 1, tile_size):
        line = scene.addLine(0, y, pixmap_width, y, pen)
        line.setZValue(z)
        grid_items.append(line)

    return grid_items

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

def apply_zoom(view, event, zoom_in=1.15):
    factor = zoom_in if event.angleDelta().y() > 0 else 1 / zoom_in
    view.scale(factor, factor)


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

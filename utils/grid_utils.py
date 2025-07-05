from PyQt5.QtWidgets import QGraphicsItem, QMessageBox
from PyQt5.QtGui import QColor, QPen
from utils.graphics_utils import draw_checkerboard_for_view


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


def draw_grid_for_view(view, tile_size: int):
    if view.pixmap_item is None:
        return
    clear_grid_for_view(view)
    view.grid_items = draw_grid_lines(
        view.scene(),
        view.pixmap_item.pixmap().width(),
        view.pixmap_item.pixmap().height(),
        tile_size
    )
    view.grid_visible = True


def clear_grid_for_view(view):
    if hasattr(view, "grid_items"):
        for item in view.grid_items:
            if isinstance(item, QGraphicsItem):
                view.scene().removeItem(item)
    view.grid_items = []
    view.grid_visible = False


def draw_grid_ui(view, tile_size_field, grid_button):
    try:
        tile_size = tile_size_field.value()
        view.set_tile_size(tile_size)
    except ValueError:
        QMessageBox.warning(view, "Errore", "Dimensione griglia non valida.")
        return

    draw_checkerboard_for_view(view, tile_size)

    if grid_button.isChecked():
        grid_button.setText("Disattiva griglia")
        draw_grid_for_view(view, tile_size)
    else:
        grid_button.setText("Attiva griglia")
        clear_grid_for_view(view)

from PyQt5.QtWidgets import QFileDialog, QGraphicsView, QMessageBox
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPixmap, QColor, QPen


class CtrlDragMixin:
    def handle_drag_press(self, event):
        if event.button() == Qt.LeftButton and (event.modifiers() & Qt.ControlModifier):
            self.setDragMode(QGraphicsView.ScrollHandDrag)

    def handle_drag_move(self, event):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.viewport().setCursor(Qt.ClosedHandCursor)

    def handle_drag_release(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self.setDragMode(QGraphicsView.NoDrag)
            self.viewport().setCursor(Qt.ArrowCursor)


class ShiftDragRectSelectMixin:
    def handle_shift_press(self, event, scene, pixmap_item):
        if event.modifiers() & Qt.ShiftModifier:
            pos = self.mapToScene(event.pos())
            if not pixmap_item or not pixmap_item.pixmap().rect().contains(int(pos.x()), int(pos.y())):
                return False

            self.drag_selecting = True
            self.drag_start_pos = pos

            if hasattr(self, "selection_rect_item") and self.selection_rect_item:
                scene.removeItem(self.selection_rect_item)

            self.selection_rect_item = scene.addRect(QRectF())
            self.selection_rect_item.setBrush(QColor(255, 165, 0, 60))  # semi-trasparente
            self.selection_rect_item.setPen(QPen(QColor(255, 165, 0), 1))  # bordo pieno
            self.selection_rect_item.setZValue(8)
            return True
        return False

    def handle_shift_move(self, event):
        if getattr(self, "drag_selecting", False) and hasattr(self, "selection_rect_item"):
            current_pos = self.mapToScene(event.pos())
            rect = QRectF(self.drag_start_pos, current_pos).normalized()
            self.selection_rect_item.setRect(rect)

    def handle_shift_release(self, event, scene, select_callback):
        if getattr(self, "drag_selecting", False) and hasattr(self, "selection_rect_item"):
            rect = self.selection_rect_item.rect()
            scene.removeItem(self.selection_rect_item)
            self.selection_rect_item = None
            self.drag_selecting = False
            select_callback(rect)


def get_snapped_rect(rect: QRectF, tile_size: int) -> QRectF:
    x1 = int(rect.left() // tile_size) * tile_size
    y1 = int(rect.top() // tile_size) * tile_size
    x2 = int((rect.right() + tile_size - 1) // tile_size) * tile_size
    y2 = int((rect.bottom() + tile_size - 1) // tile_size) * tile_size
    return QRectF(x1, y1, x2 - x1, y2 - y1)

def apply_zoom(view, event, zoom_in=1.15):
    factor = zoom_in if event.angleDelta().y() > 0 else 1 / zoom_in
    view.scale(factor, factor)


def load_pixmap(parent, pixmap: QPixmap = None) -> QPixmap:
    if pixmap:
        return pixmap

    file_path, _ = QFileDialog.getOpenFileName(parent, "Apri immagine", "", "Immagini (*.png *.jpg *.bmp)")
    if not file_path:
        return None

    loaded_pixmap = QPixmap(file_path)
    if loaded_pixmap.isNull():
        QMessageBox.warning(parent, "Errore", "Immagine non valida.")
        return None

    return loaded_pixmap


def save_pixmap_dialog(parent, pixmap: QPixmap, label="immagine"):
    if not pixmap or pixmap.isNull():
        QMessageBox.warning(parent, "Errore", "Nessuna immagine da salvare.")
        return

    file_path, _ = QFileDialog.getSaveFileName(
        parent,
        "Salva immagine",
        f"{label}.png",
        "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)"
    )
    if file_path:
        pixmap.save(file_path)
        QMessageBox.information(parent, "Salvataggio completato", "Immagine salvata con successo.")




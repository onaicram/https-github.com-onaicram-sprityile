from PyQt5.QtWidgets import QFileDialog, QGraphicsView, QMessageBox, QGraphicsPixmapItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QColor, QPainter

class BasicDragMixin:
    def handle_drag_press(self, event):
        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)

    def handle_drag_move(self, event):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.viewport().setCursor(Qt.ClosedHandCursor)

    def handle_drag_release(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self.setDragMode(QGraphicsView.NoDrag)
            self.viewport().setCursor(Qt.ArrowCursor)


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




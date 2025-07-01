from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMessageBox

def save_state(pixmap_item, undo_stack: list, redo_stack: list):
    if pixmap_item and pixmap_item.pixmap():
        undo_stack.append(pixmap_item.pixmap().copy())
        redo_stack.clear()

def undo(pixmap_item, undo_stack: list, redo_stack: list):
    if len(undo_stack) > 1:
        current = undo_stack.pop()
        redo_stack.append(current)
        previous = undo_stack[-1]
        pixmap_item.setPixmap(previous)

def redo(pixmap_item, undo_stack: list, redo_stack: list):
    if redo_stack:
        next_state = redo_stack.pop()
        undo_stack.append(next_state)
        pixmap_item.setPixmap(next_state)

def reset_image(pixmap_item, original_pixmap: QPixmap, undo_stack: list, redo_stack: list, color_field=None, parent=None):
    if original_pixmap and pixmap_item:
        pixmap_item.setPixmap(QPixmap(original_pixmap))
        undo_stack.clear()
        redo_stack.clear()
        undo_stack.append(QPixmap(original_pixmap))
        if color_field:
            color_field.setText("Nessun colore")
        if parent:
            QMessageBox.information(parent, "Reset", "Immagine ripristinata.")

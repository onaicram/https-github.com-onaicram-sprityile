import sys
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QFileDialog, QMainWindow, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage, QBrush
from PyQt5.QtCore import Qt, QRectF, pyqtSignal


class ImageViewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sprityle")
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.pixmap_item = None
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(Qt.lightGray))
     
    def drawBackground(self, painter, rect):
        tile_size = 16
        color1 = QColor(220, 220, 220)
        color2 = QColor(255, 255, 255)

        left = int(rect.left())
        top = int(rect.top())
        right = int(rect.right())
        bottom = int(rect.bottom())

        for y in range(top, bottom, tile_size):
            for x in range(left, right, tile_size):
                if ((x // tile_size) + (y // tile_size)) % 2 == 0:
                    painter.fillRect(x, y, tile_size, tile_size, color1)
                else:
                    painter.fillRect(x, y, tile_size, tile_size, color2)


    color_picked = pyqtSignal(str)
    def mousePressEvent(self, event):
        if self.pixmap_item is None:
            return

        pos = self.mapToScene(event.pos())
        x, y = int(pos.x()), int(pos.y())

        if 0 <= x < self.pixmap_item.pixmap().width() and 0 <= y < self.pixmap_item.pixmap().height():
            image = self.pixmap_item.pixmap().toImage()
            color = image.pixelColor(x, y)
            hex_color = color.name().upper()
            self.color_picked.emit(hex_color)

        self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.setCursor(Qt.ClosedHandCursor)
        super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        self.setDragMode(QGraphicsView.NoDrag)
        self.setCursor(Qt.ArrowCursor)  
        super().mouseReleaseEvent(event)


    def load_image(self, image_path):
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print("Errore: immagine non valida")
            return

        self.scene.clear()

        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)

        self.setSceneRect(QRectF(pixmap.rect()))
        self.resetTransform()
        

        # Adatta la vista alle dimensioni
        view_width = self.viewport().width()
        view_height = self.viewport().height()
        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()

        scale_x = view_width / pixmap_width
        scale_y = view_height / pixmap_height
        scale = min(scale_x, scale_y) * 0.9

        self.scale(scale, scale)


    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        zoom = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
        self.scale(zoom, zoom)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.undo_stack = []
        self.redo_stack = []

        self.setWindowTitle("Sprityle")

        self.viewer = ImageViewer()
        self.original_pixmap = None  # Per l'undo

        self.viewer.color_picked.connect(self.show_color)

        self.load_button = QPushButton("Carica immagine")
        self.load_button.setMaximumWidth(120)
        self.load_button.clicked.connect(self.load_image)

        self.color_label = QLabel("Colore selezionato:")
        self.color_label.setFixedWidth(120)

        self.color_field = QLineEdit("Nessun colore")
        self.color_field.setFixedWidth(80)
        self.color_field.setReadOnly(True)

        self.copy_button = QPushButton("Copia")
        self.copy_button.setFixedWidth(60)
        self.copy_button.clicked.connect(self.copy_color)

        self.remove_color_button = QPushButton("Rimuovi colore")
        self.remove_color_button.setFixedWidth(120)
        self.remove_color_button.clicked.connect(self.remove_selected_color)

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
        self.reset_button.clicked.connect(self.reset_image)

        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_field)
        color_layout.addWidget(self.copy_button)
        color_layout.addWidget(self.remove_color_button)

        layout = QVBoxLayout()
        layout.addWidget(self.viewer)
        layout.addLayout(color_layout)

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

    def remove_selected_color(self):
        if self.viewer.pixmap_item is None:
            return
        
        image = self.viewer.pixmap_item.pixmap().toImage() 

        color_hex = self.color_field.text()
        if not color_hex or color_hex == "Nessun colore":
            return

        target_color = QColor(color_hex)
        changed = False
        
        for y in range(image.height()):
            for x in range(image.width()):
                if image.pixelColor(x, y) == target_color:
                    image.setPixelColor(x, y, QColor(0, 0, 0, 0))
                    changed = True

        if changed:
            self.viewer.pixmap_item.setPixmap(QPixmap.fromImage(image))
            self.save_state()

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Apri immagine", "", "Immagini (*.png *.jpg *.bmp)")
        if file_path:
            self.viewer.load_image(file_path)
            self.undo_stack.clear()
            self.redo_stack.clear()
            self.save_state()

    def save_image(self):
        if self.viewer.pixmap_item is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salva immagine", "", "PNG (*.png);;JPEG (*.jpg *.jpeg)"
        )
        if file_path:
            self.viewer.pixmap_item.pixmap().save(file_path)
            QMessageBox.information(self, "Salvataggio completato", "Immagine salvata con successo.")

    def reset_image(self):
        if self.original_pixmap and self.viewer.pixmap_item:
            self.viewer.pixmap_item.setPixmap(self.original_pixmap)
            QMessageBox.information(self, "Reset", "Immagine ripristinata.")


    def save_state(self):
        if self.viewer.pixmap_item:
            pixmap = self.viewer.pixmap_item.pixmap().copy()
            self.undo_stack.append(pixmap)
            self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) > 1:
            current = self.undo_stack.pop()
            self.redo_stack.append(current)
            prev = self.undo_stack[-1]
            self.viewer.pixmap_item.setPixmap(prev)

    def redo(self):
        if self.redo_stack:
            next_state = self.redo_stack.pop()
            self.undo_stack.append(next_state)
            self.viewer.pixmap_item.setPixmap(next_state)


    def show_color(self, hex_color):
        self.color_field.setText(hex_color)


    def copy_color(self):
        color = self.color_field.text()
        if color and color != "Nessun colore":
            clipboard = QApplication.clipboard()
            clipboard.setText(color)
            QMessageBox.information(self, "Colore copiato", f"{color} copiato negli appunti.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec_())

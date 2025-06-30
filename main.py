import sys
from PyQt5.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QFileDialog, QMainWindow, QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage
from PyQt5.QtCore import Qt, QRectF, pyqtSignal

from tile_splitter import TileSplitterWindow


class ImageViewer(QGraphicsView):
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


    def load_image(self, image_path, tile_size=16):
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print("Errore: immagine non valida")
            return

        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.pixmap_item.setZValue(1)  # Assicura che l'immagine sia sopra la griglia
        self.scene.addItem(self.pixmap_item)

        self.draw_checkerboard(pixmap, tile_size)

        self.setSceneRect(QRectF(pixmap.rect()))
        self.resetTransform()
        self.centerOn(self.pixmap_item)
        
        # Adatta la vista alle dimensioni
        view_width = self.viewport().width()
        view_height = self.viewport().height()
        pixmap_width = pixmap.width()
        pixmap_height = pixmap.height()

        scale_x = view_width / pixmap_width
        scale_y = view_height / pixmap_height
        scale = min(scale_x, scale_y) * 0.9

        self.scale(scale, scale)


    def draw_checkerboard(self, pixmap, checker_size=16):
        
        image_width, image_height = pixmap.width(), pixmap.height()
        checkerboard = QPixmap(image_width, image_height)
        checkerboard.fill(Qt.transparent)
        painter = QPainter(checkerboard)
        color1 = QColor(200, 200, 200)
        color2 = QColor(255, 255, 255)

        for y in range(0, image_height, checker_size):
            for x in range(0, image_width, checker_size):
                color = color1 if ((x // checker_size + y // checker_size) % 2 == 0) else color2
                painter.fillRect(x, y, checker_size, checker_size, color)
        painter.end()

        checker_item = QGraphicsPixmapItem(checkerboard)
        checker_item.setZValue(0)  # Assicura che il checkerboard sia sotto l'immagine
        self.scene.addItem(checker_item)


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
        self.current_tile_size = 16  # Dimensione predefinita dei tasselli

        self.setWindowTitle("Sprityle")

        self.viewer = ImageViewer()
        self.original_pixmap = None  
        self.viewer.color_picked.connect(self.show_color)

        self.tile_splitter_button = QPushButton("Gestisci tasselli")
        self.tile_splitter_button.setFixedWidth(120)
        self.tile_splitter_button.clicked.connect(self.open_tile_splitter)

        self.tile_splitter_layout= QHBoxLayout()
        self.tile_splitter_layout.addWidget(self.tile_splitter_button)
        self.tile_splitter_layout.setAlignment(Qt.AlignCenter)

        # Color 
        self.color_label = QLabel("Colore selezionato:")
        self.color_label.setMaximumWidth(90)

        self.color_field = QLineEdit("Nessun colore")
        self.color_field.setFixedWidth(80)
        self.color_field.setReadOnly(True)

        self.copy_button = QPushButton("Copia")
        self.copy_button.setFixedWidth(80)
        self.copy_button.clicked.connect(self.copy_color)

        self.remove_color_button = QPushButton("Rimuovi colore")
        self.remove_color_button.setFixedWidth(120)
        self.remove_color_button.clicked.connect(self.remove_selected_color)

        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_label)
        color_layout.addWidget(self.color_field)
        color_layout.addWidget(self.copy_button)
        color_layout.addWidget(self.remove_color_button)
        color_layout.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addLayout(self.tile_splitter_layout)
        layout.addWidget(self.viewer)
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
        self.reset_button.clicked.connect(self.reset_image)

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


    def open_tile_splitter(self):
        if self.viewer.pixmap_item is None:
            QMessageBox.warning(self, "Errore", "Nessuna immagine caricata.")
            return

        pixmap = self.viewer.pixmap_item.pixmap().copy()

        self.tile_splitter = TileSplitterWindow(pixmap)
        self.tile_splitter.show()


    def remove_selected_color(self):
        if self.viewer.pixmap_item is None:
            return
        
        original_pixmap = self.viewer.pixmap_item.pixmap()
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
            self.viewer.pixmap_item.setPixmap(QPixmap.fromImage(image))
            self.save_state()

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Apri immagine", "", "Immagini (*.png *.jpg *.bmp)")
        if file_path:

            tile_size = int(self.current_tile_size)
            
            self.viewer.load_image(file_path, tile_size)
            self.original_pixmap = self.viewer.pixmap_item.pixmap().copy()
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
            # Ripristina l'immagine originale
            self.viewer.pixmap_item.setPixmap(QPixmap(self.original_pixmap))

            # Pulisce gli stack di undo e redo
            self.undo_stack.clear()
            self.redo_stack.clear()

            # Aggiorna lo stato visivo e informa l'utente
            self.color_field.setText("Nessun colore")
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

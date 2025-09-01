from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

class ToolBox(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.select_button = QPushButton("Seleziona 🖱️")
        self.ruler_button = QPushButton("Righello 📏")
        self.draw_button = QPushButton("Disegna ✏️")
        self.pick_button = QPushButton("Pick 🎯")
        self.delete_button = QPushButton("Cancella 🗑️")

        layout = QVBoxLayout()
        
        layout.addWidget(self.select_button)
        layout.addWidget(self.ruler_button)
        layout.addWidget(self.draw_button)
        layout.addWidget(self.pick_button)
        layout.addWidget(self.delete_button)
        layout.addStretch()

        self.setLayout(layout)

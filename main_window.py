from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
                                QApplication, QMessageBox, QGridLayout, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

import os
from utils.graphics_utils import load_image_with_checker, create_section
from utils.controls_utils import save_pixmap_dialog
from utils.grid_utils import draw_grid_for_view, clear_grid_for_view, draw_checkerboard_for_view
from utils.states_utils import undo_state, redo_state, reset_state, save_state
from utils.meta_utils import MetaUtils

from ui.info_bar import InfoBar
from ui.tool_box import ToolBox
from ui.work_view import WorkView
from ui.color_box import ColorBox 
from ui.state_bar import StateBar
from ui.grid_box import GridBox
from ui.save_menu import SaveMenu
from ui.tab_menu import TabMenu


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sprityle - Editor di Sprite")
        self._current_filename = ""

        self.undo_stack = []
        self.redo_stack = []
        self.current_tile_size = 16
        self.original_pixmap = None

        # --- UI Elements ---
        self.info_bar = InfoBar()
        self.info_bar.set_mode("select")

        self.tool_box = ToolBox()
        self.tool_box.select_button.clicked.connect(lambda: self.work_view.set_mode("select"))
        self.tool_box.ruler_button.clicked.connect(lambda: self.work_view.set_mode("ruler"))
        self.tool_box.draw_button.clicked.connect(lambda: self.work_view.set_mode("draw"))
        self.tool_box.pick_button.clicked.connect(lambda: self.work_view.set_mode("picker"))
        self.tool_box.delete_button.clicked.connect(lambda: self.work_view.set_mode("delete"))

        self.grid_box = GridBox()
        self.grid_box.grid_changed.connect(self.on_grid_toggle)

        self.color_box = ColorBox()
        self.color_box.color_changed.connect(self.on_color_changed)
        self.color_box.color_removed.connect(self.on_color_removed)
        self.color_box.color_copied.connect(self.on_color_copied)

        self.work_view = WorkView()
        self.work_view.mode_changed.connect(self.info_bar.set_mode)
        self.work_view.color_picked.connect(self.color_box.set_color)

        self.tab_menu = TabMenu(self.work_view)

        self.state_bar = StateBar()
        self.state_bar.undo_requested.connect(self.on_undo)
        self.state_bar.redo_requested.connect(self.on_redo)
        self.state_bar.reset_requested.connect(self.on_reset)

        self.save_menu = SaveMenu()
        self.save_menu.load_requested.connect(self.on_load_image)
        self.save_menu.save_requested.connect(self.on_save_image)
        self.save_menu.export_requested.connect(self.work_view.export_selection)

        # FINAL LAYOUT
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # MAIN LAYOUT
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # CENTRAL GRID LAYOUT
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(10, 10, 5, 0)  # margini 
        grid_layout.setHorizontalSpacing(10) # spazio fra colonne
        grid_layout.setColumnStretch(0, 1)   # Colonna ToolBox
        grid_layout.setColumnStretch(1, 4)   # WorkView centrale
        grid_layout.setColumnStretch(2, 1)   # Frame view a destra

        # LABEL ESTERNA: Strumenti
        label_tool = QLabel("🛠️ Strumenti")
        label_tool.setAlignment(Qt.AlignHCenter)

        # SEZIONI BOXATE
        tool_section = create_section("Modalità", self.tool_box)
        grid_section = create_section("Griglia", self.grid_box)
        color_section = create_section("Colore", self.color_box)

        # LAYOUT COLONNA SINISTRA
        side_layout = QVBoxLayout()
        side_layout.setContentsMargins(0, 18, 0, 0)
        side_layout.setSpacing(10)
        side_layout.addWidget(label_tool)
        side_layout.addWidget(tool_section)
        side_layout.addWidget(grid_section)
        side_layout.addWidget(color_section)
        side_layout.addStretch()

        side_widget = QWidget()
        side_widget.setLayout(side_layout)
        side_widget.setMaximumWidth(140)
        side_widget.setFixedWidth(140)

        # Central column: TabMenu above and WorkView below
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(6)
        center_layout.addWidget(self.tab_menu)
        center_layout.addWidget(self.info_bar)

        center_widget = QWidget()
        center_widget.setLayout(center_layout)

        # RIGHT COLUMN (Frame View)
        frame_view_label = QLabel("🧩 Frame View")
        frame_view_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        
        framne_widget = QWidget()
        frame_layout = QVBoxLayout(framne_widget)
        frame_layout.addWidget(frame_view_label)
        frame_layout.addStretch()
        frame_layout.setContentsMargins(0, 18, 0, 0)
        frame_layout.setSpacing(100)

        framne_widget.setFixedWidth(140)

        grid_layout.addWidget(side_widget, 0, 0)
        grid_layout.addWidget(center_widget, 0, 1)
        grid_layout.addWidget(framne_widget, 0, 2)

        grid_widget = QWidget()
        grid_widget.setLayout(grid_layout)
        main_layout.addWidget(grid_widget)

        # BOTTOM LAYOUT
        self.coord_label = QLabel("Pixel: (0,0)  Tile: (0,0)")
        self.coord_label.setFixedWidth(200) 
        self.coord_label.setAlignment(Qt.AlignCenter)
        self.coord_label.setStyleSheet("font-family: monospace;")

        bottom_bar_layout = QHBoxLayout()
        bottom_bar_layout.setContentsMargins(6, 2, 6, 2)
        bottom_bar_layout.setSpacing(10)
        bottom_bar_layout.addWidget(self.save_menu)
        bottom_bar_layout.addStretch(1)
        bottom_bar_layout.addWidget(self.coord_label)
        bottom_bar_layout.addStretch(1)
        bottom_bar_layout.addWidget(self.state_bar)
    
        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_bar_layout)
        main_layout.addWidget(bottom_widget)


    def set_filename(self, filename: str):
        self._current_filename = filename
        self.setWindowTitle(f"Sprityle - {filename}")

    def on_load_image(self):

        clear_grid_for_view(self.work_view)

        tile_size = 16 

        pixmap_item = load_image_with_checker(
            view=self.work_view,
            scene=self.work_view.scene,
            pixmap=None,
            parent=self,
            tile_size=tile_size
        )

        if pixmap_item:
            self.work_view.set_pixmap_item(pixmap_item)
            filename = getattr(pixmap_item, "path", "Senza nome")
            self.set_filename(os.path.basename(filename))
            self.original_pixmap = pixmap_item.pixmap().copy()
            self.undo_stack.clear()
            self.redo_stack.clear()

            save_state(
                pixmap_item,
                self.work_view.selected_tiles if self.work_view.grid_visible else self.work_view.selected_pixels,
                self.undo_stack,
                self.redo_stack
            )

    def on_grid_toggle(self, active: bool, tile_size: int):
        self.work_view.set_tile_size(tile_size)
        draw_checkerboard_for_view(self.work_view, tile_size)

        if active:
            draw_grid_for_view(self.work_view, tile_size)
            self.info_bar.set_grid_status("ON")
            self.save_menu.set_export_enabled(True)
        else:
            clear_grid_for_view(self.work_view)
            self.work_view._clear_all_selection()
            self.info_bar.set_grid_status("OFF")
            self.save_menu.set_export_enabled(False)

    def on_save_image(self):
        if not self.work_view.pixmap_item:
            return

        pixmap = self.work_view.pixmap_item.pixmap()
        path = save_pixmap_dialog(self, pixmap, "immagine")
        if path:
            self.set_filename(os.path.basename(path))
            MetaUtils.save_meta(path, tile_size=16, editable=True)

    def on_color_changed(self, color: QColor):
        self.work_view.current_color = color
        
    def on_color_removed(self):
        if self.work_view.pixmap_item is None:
            return

        self.work_view.remove_color()
        self.color_box.clear_color()

    def on_color_copied(self, hex_color: str):
        clipboard = QApplication.clipboard()
        clipboard.setText(hex_color)
        QMessageBox.information(self, "Colore copiato", f"{hex_color} copiato negli appunti.")

    def on_undo(self):
        undo_state(
            self.work_view.pixmap_item,
            self.work_view.selected_tiles if self.work_view.grid_visible else self.work_view.selected_pixels,
            self.undo_stack,
            self.redo_stack,
            self.work_view.restore_tile_selection if self.work_view.grid_visible else self.work_view.restore_pixel_selection
        )
        
    def on_redo(self):
        redo_state(
            self.work_view.pixmap_item,
            self.work_view.selected_tiles if self.work_view.grid_visible else self.work_view.selected_pixels,
            self.undo_stack,
            self.redo_stack,
            self.work_view.restore_tile_selection if self.work_view.grid_visible else self.work_view.restore_pixel_selection
        )
        

    def on_reset(self):
        reset_state(
            self.work_view.pixmap_item,
            self.original_pixmap,
            self.work_view.selected_tiles,
            self.undo_stack,
            self.redo_stack,
            restore_selection_fn=self.work_view.restore_selection,
            parent=self
        )

    def update_coordinates(self, px, py, tx, ty, extra=""):
        text = f"Pixel: ({px},{py})  Tile: ({tx},{ty})"
        if extra:
            text += f"  |  {extra}"
        self.coord_label.setText(text)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec_())

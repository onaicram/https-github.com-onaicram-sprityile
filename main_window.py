from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication, QMessageBox, QLabel
from PyQt5.QtGui import QColor

import os
from utils.graphics_utils import load_image_with_checker
from utils.controls_utils import save_pixmap_dialog
from utils.grid_utils import draw_grid_for_view, clear_grid_for_view, draw_checkerboard_for_view
from utils.states_utils import undo_state, redo_state, reset_state, save_state
from utils.meta_utils import MetaUtils

from ui.info_bar import InfoBar
from ui.tool_bar import ToolBar
from ui.work_view import WorkView
from ui.color_box import ColorBox 
from ui.state_bar import StateBar
from ui.grid_box import GridBox
from ui.save_bar import SaveBar


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

        self.tool_bar = ToolBar()
        self.tool_bar.select_button.clicked.connect(lambda: self.work_view.set_mode("select"))
        self.tool_bar.draw_button.clicked.connect(lambda: self.work_view.set_mode("draw"))
        self.tool_bar.pick_button.clicked.connect(lambda: self.work_view.set_mode("picker"))
        self.tool_bar.delete_button.clicked.connect(lambda: self.work_view.set_mode("delete"))

        self.grid_box = GridBox()
        self.grid_box.grid_changed.connect(self.on_grid_toggle)

        self.color_box = ColorBox()
        self.color_box.color_changed.connect(self.on_color_changed)
        self.color_box.color_removed.connect(self.on_color_removed)
        self.color_box.color_copied.connect(self.on_color_copied)

        self.work_view = WorkView()
        self.work_view.mode_changed.connect(self.info_bar.set_mode)
        self.work_view.color_picked.connect(self.color_box.set_color)

        self.state_bar = StateBar()
        self.state_bar.undo_requested.connect(self.on_undo)
        self.state_bar.redo_requested.connect(self.on_redo)
        self.state_bar.reset_requested.connect(self.on_reset)

        self.save_bar = SaveBar()
        self.save_bar.load_requested.connect(self.on_load_image)
        self.save_bar.save_requested.connect(self.on_save_image)

        self.frame_player_placeholder = QLabel("🎞️ Frame Player (prossimamente)")
        self.frame_player_placeholder.setMinimumHeight(40)
        self.frame_player_placeholder.setStyleSheet("background-color: #ddd; padding: 5px;")

        main_layout = QVBoxLayout()
        
        # Central widget to hold the main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setLayout(main_layout)

        # Side layout for ToolBar and ColorBox
        side_layout = QVBoxLayout()
        side_layout.addWidget(self.tool_bar)
        side_layout.addStretch(1) 
        side_layout.addWidget(self.grid_box)
        side_layout.addStretch(1)
        side_layout.addWidget(self.color_box)

        # Center Area
        center_layout = QHBoxLayout()
        center_layout.addLayout(side_layout)
        center_layout.addWidget(self.work_view, stretch=1)
        
        # Bottom Layout
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.frame_player_placeholder)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.save_bar)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.state_bar)

        # Assemble the main layout
        main_layout.addWidget(self.info_bar)
        main_layout.addLayout(center_layout)
        main_layout.addLayout(bottom_layout)


    def set_filename(self, filename: str):
        self._current_filename = filename
        self.setWindowTitle(f"Sprityle – {filename}")

    def on_load_image(self):

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
        else:
            clear_grid_for_view(self.work_view)
            self.work_view._clear_all_selection()
            self.info_bar.set_grid_status("OFF")

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


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec_())

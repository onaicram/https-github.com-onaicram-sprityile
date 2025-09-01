from PyQt5.QtWidgets import QTabWidget, QWidget

class TabMenu(QTabWidget):
    def __init__(self, work_view: QWidget, atlas: QWidget = None):
        super().__init__()

        self.work_view = work_view
        self.atlas = atlas or QWidget()

        self.addTab(self.work_view, "🖼️ Main")
        self.addTab(self.atlas, "🗺️ Atlas")

         

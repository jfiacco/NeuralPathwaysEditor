from qtpy.QtWidgets import QMainWindow, QAction
from qtpy.QtCore import Slot

from NeuralPathways.ui.tabs import AppTabs

class PathwaysMainWindow(QMainWindow):

    def __init__(self):
        super().__init__(parent=None)
        self.title = 'Neural Pathways Explorer'
        self.left = 100
        self.top = 100
        self.width = 1280
        self.height = 720
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.table_widget = AppTabs(self)
        self.setCentralWidget(self.table_widget)
        self.addMenu()

        self.show()

    def addMenu(self):
        menuBar = self.menuBar()

        # Add menu items
        fileMenu = menuBar.addMenu('File')
        editMenu = menuBar.addMenu('Edit')
        helpMenu = menuBar.addMenu('Help')

        visitWebsiteAction = QAction('Visit Our Website', self)
        fileBugReportAction = QAction('File a Bug Report', self)

        helpMenu.addAction(visitWebsiteAction)
        helpMenu.addAction(fileBugReportAction)

    @Slot()
    def on_click(self):
        print("\n")
        for currentQTableWidgetItem in self.tableWidget.selectedItems():
            print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())
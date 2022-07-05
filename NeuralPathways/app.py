from qtpy.QtWidgets import QApplication

from NeuralPathways.ui.mainWindow import PathwaysMainWindow

class PathwaysApp:

    def __init__(self, argv):
        self.argv = argv
        self.app = QApplication(self.argv)
        self.window = PathwaysMainWindow()

    def run(self):
        self.app.exec_()

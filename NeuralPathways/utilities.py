from qtpy.QtCore import QObject, Signal
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT


class SignalBridge(QObject):
    valueUpdated = Signal()

    def __init__(self):
        QObject.__init__(self)

    def sendSignal(self):
        self.valueUpdated.emit()

class NavigationToolbar(NavigationToolbar2QT):
    # only display the buttons we need
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Save')]
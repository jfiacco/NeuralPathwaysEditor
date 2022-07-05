import pandas as pd

from qtpy import QtWidgets

import NeuralPathways.session as s

from NeuralPathways.models.pandas_model import PandasModel
from NeuralPathways.utilities import SignalBridge


class AttributeWidget(QtWidgets.QWidget):

    def __init__(self, bridge, parent=None):
        QtWidgets.QWidget.__init__(self, parent=None)

        self.bridge = bridge

        vLayout = QtWidgets.QVBoxLayout(self)
        hLayout = QtWidgets.QHBoxLayout()
        self.pathLE = QtWidgets.QLineEdit(self)
        hLayout.addWidget(self.pathLE)
        self.loadBtn = QtWidgets.QPushButton("Select File", self)
        hLayout.addWidget(self.loadBtn)
        vLayout.addLayout(hLayout)
        self.pandasTv = QtWidgets.QTableView(self)
        vLayout.addWidget(self.pandasTv)
        self.loadBtn.clicked.connect(self.loadFile)
        self.pandasTv.setSortingEnabled(True)

    def loadFile(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv)");
        self.pathLE.setText(fileName)
        try:
            df = pd.read_csv(fileName)
        except FileNotFoundError as e:
            return
        s.ATTRIBUTE_MODEL = PandasModel(df)
        self.pandasTv.setModel(s.ATTRIBUTE_MODEL)
        self.bridge.sendSignal()
        s.sig_attribute_loaded.sendSignal()

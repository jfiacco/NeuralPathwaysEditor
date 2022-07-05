import json
import numpy as np
import pandas as pd

from qtpy import QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QTreeView
from qtpy.QtGui import QStandardItemModel, QStandardItem

import NeuralPathways.session as s
import NeuralPathways.pathways as p

class ActivationWidget(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self, parent=None)

        hLayoutFull = QtWidgets.QHBoxLayout(self)

        # Create layout for loading and viewing activations from JSON file
        vLayoutActivations = QtWidgets.QVBoxLayout()
        hLayoutLoadFile = QtWidgets.QHBoxLayout()
        self.pathLE = QtWidgets.QLineEdit(self)
        hLayoutLoadFile.addWidget(self.pathLE)

        self.loadBtn = QtWidgets.QPushButton("Select File", self)
        hLayoutLoadFile.addWidget(self.loadBtn)
        self.loadBtn.clicked.connect(self.loadFile)

        vLayoutActivations.addLayout(hLayoutLoadFile)
        self.activationView = QTreeView()
        vLayoutActivations.addWidget(self.activationView)

        hLayoutFull.addLayout(vLayoutActivations, 2)

        # Create layout for extracting pathways
        vLayoutExtraction = QtWidgets.QVBoxLayout()

        self.dimReductionLbl = QtWidgets.QLabel("Dimensionality Reduction Technique:")
        vLayoutExtraction.addWidget(self.dimReductionLbl)

        self.dimReductionChoiceBox = QtWidgets.QComboBox()
        self.dimReductionChoiceBox.addItems(["PCA"])
        vLayoutExtraction.addWidget(self.dimReductionChoiceBox)
        self.dimReductionChoiceBox.currentTextChanged.connect(self.chooseDimensionalityReduction)

        self.varianceLbl = QtWidgets.QLabel("Percent Explained Variance: (default = 75%)")
        vLayoutExtraction.addWidget(self.varianceLbl)

        hLayoutVariance = QtWidgets.QHBoxLayout()
        self.varianceSlider = QtWidgets.QSlider(Qt.Horizontal, self)

        self.varianceSlider.setMinimum(1)
        self.varianceSlider.setMaximum(99)
        self.varianceSlider.setSingleStep(1)
        self.varianceSlider.setValue(75)
        hLayoutVariance.addWidget(self.varianceSlider)
        s.TOTAL_EXPLAINED_VARIANCE = self.varianceSlider.value() / 100
        self.varianceSlider.valueChanged.connect(self.sliderValueChanged)
        self.varianceSlider.sliderReleased.connect(self.sliderReleased)
        self.varianceSelectedLbl = QtWidgets.QLabel("{}%".format(self.varianceSlider.value()))
        hLayoutVariance.addWidget(self.varianceSelectedLbl)
        vLayoutExtraction.addLayout(hLayoutVariance)

        vLayoutExtraction.addStretch()

        pathways_info = s.PATHWAYS_INFO_MODEL.df.columns
        self.pathwaysInfoModel = QStandardItemModel(len(pathways_info), 2)
        self.pathwaysInfoModel.setHeaderData(0, Qt.Horizontal, "Pathway")
        self.pathwaysInfoModel.setHeaderData(1, Qt.Horizontal, "% Variance Explained")

        self.pathwaysInfoView = QtWidgets.QTreeView()
        self.pathwaysInfoView.setModel(self.pathwaysInfoModel)
        self.pathwaysInfoView.setAlternatingRowColors(True)

        vLayoutExtraction.addWidget(self.pathwaysInfoView)

        if s.ACTIVATION_MATRIX is None:
            self.extractionReadyLbl = QtWidgets.QLabel("Waiting for file...")
        else:
            self.extractionReadyLbl = QtWidgets.QLabel("Ready for extraction.")

        vLayoutExtraction.addWidget(self.extractionReadyLbl)

        self.extractBtn = QtWidgets.QPushButton("Extract Pathways", self)
        self.extractBtn.setMinimumWidth(200)
        vLayoutExtraction.addWidget(self.extractBtn)
        self.extractBtn.clicked.connect(self.extractPathways)

        hLayoutFull.addLayout(vLayoutExtraction, 1)

        self.activationView.setAlternatingRowColors(True)


    def loadFile(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "", "JSON Files (*.json)")
        self.pathLE.setText(fileName)
        try:
            with open(fileName) as file:
                document = json.load(file)

        except FileNotFoundError as e:
            return

        if s.ACTIVATION_MATRIX is not None:
            self.extractionReadyLbl.setText("New file loaded. Ready for extraction.")
        else:
            self.extractionReadyLbl.setText("Ready for extraction.")
        s.ACTIVATION_DICT = document
        s.ACTIVATION_MATRIX, s.ACTIVATION_NEURONS = self._createActivationMatrix(document)
        s.ACTIVATION_MODEL = QStandardItemModel(s.ACTIVATION_MATRIX.shape[0], len(s.ACTIVATION_NEURONS))
        s.ACTIVATION_MODEL.clear()
        print(s.ACTIVATION_MATRIX.shape)

        for row in s.ACTIVATION_MATRIX:
            s.ACTIVATION_MODEL.appendRow(tuple([QStandardItem(f"{n:.04f}") for n in row]))

        for i, neuron in enumerate(s.ACTIVATION_NEURONS):
            s.ACTIVATION_MODEL.setHeaderData(i, Qt.Horizontal, neuron)

        self.activationView.setModel(s.ACTIVATION_MODEL)


    def _createActivationMatrix(self, d):
        if d is None:
            return

        arrs = []
        column_names = []
        for k, v in d.items():
            if len(v) == 0:
                print('Skipping {} because there are no data instances.'.format(k))
                continue
            elif v[0] == 0:
                print('Skipping {} because there are no neurons.'.format(k))
                continue

            temp_arr = np.zeros((len(v), len(v[0])))
            column_names.extend([f"{k}:{n}" for n in range(len(v[0]))])
            for i, neurons in enumerate(v):
                for j, activation in enumerate(neurons):
                    temp_arr[i, j] = activation

            arrs.append(temp_arr)

        return np.concatenate(arrs, axis=1), column_names


    def extractPathways(self):
        if s.ACTIVATION_MATRIX is None:
            self.extractionReadyLbl.setText("ERROR: Need to load activations. Waiting for file...")
            return

        self.extractionReadyLbl.setText("PROCESSING: Please wait...")
        result = p.extract_pathways()

        if result is None:
            return
        num_pathways, _ = result
        self.extractionReadyLbl.setText("DONE: {} pathway{} extracted.".
                                        format(num_pathways,
                                               '' if num_pathways == 1 else 's'))

        self.pathwaysInfoModel.clear()


        for i, v in zip(range(s.PATHWAYS_MODEL.n_components_), s.PATHWAYS_MODEL.explained_variance_ratio_):
            print(i,v)
            self.pathwaysInfoModel.appendRow((QStandardItem(str(i)), QStandardItem(f"{v*100:.03f}%")))

        self.pathwaysInfoModel.setHeaderData(0, Qt.Horizontal, "Pathway")
        self.pathwaysInfoModel.setHeaderData(1, Qt.Horizontal, "% Variance Explained")
        self.pathwaysInfoView.repaint()




    def sliderValueChanged(self):
        self.varianceSelectedLbl.setText("{}%".format(self.varianceSlider.value()))

    def sliderReleased(self):
        s.TOTAL_EXPLAINED_VARIANCE = self.varianceSlider.value() / 100

    def chooseDimensionalityReduction(self, s):
        s.DIMENSIONALITY_REDUCTION = s

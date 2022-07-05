import numpy as np

from collections import OrderedDict
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from qtpy import QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtGui import QStandardItemModel, QStandardItem

import NeuralPathways.session as s
import NeuralPathways.pathways as p

from NeuralPathways.utilities import NavigationToolbar


class AnalysisWidget(QtWidgets.QWidget):

    def __init__(self, bridge, parent=None):
        QtWidgets.QWidget.__init__(self, parent=None)

        sb = bridge
        sb.valueUpdated.connect(self.on_attribute_loaded)

        hLayoutFull = QtWidgets.QHBoxLayout(self)

        # Properties Sidebar
        vLayoutProperties = QtWidgets.QVBoxLayout()

        attributes = s.ATTRIBUTE_MODEL.df.columns
        self.attributesListModel = QStandardItemModel(len(attributes), 2)
        self.attributesListModel.setHeaderData(0, Qt.Horizontal, "Attributes")
        self.attributesListModel.setHeaderData(1, Qt.Horizontal, "Threshold")

        self.attributesListView = QtWidgets.QTreeView()
        self.attributesListView.setModel(self.attributesListModel)
        self.attributesListView.setAlternatingRowColors(True)


        self.goldLabelLbl = QtWidgets.QLabel("Gold Label Column:")

        self.goldLabelChoiceBox = QtWidgets.QComboBox()
        self.goldLabelChoiceBox.addItems(['<None Selected>'])

        self.predLabelLbl = QtWidgets.QLabel("Model Predictions Column:")
        self.predLabelChoiceBox = QtWidgets.QComboBox()
        self.predLabelChoiceBox.addItems(['<None Selected>'])

        vLayoutProperties.addWidget(self.attributesListView)
        vLayoutProperties.addWidget(self.goldLabelLbl)
        vLayoutProperties.addWidget(self.goldLabelChoiceBox)
        vLayoutProperties.addWidget(self.predLabelLbl)
        vLayoutProperties.addWidget(self.predLabelChoiceBox)

        self.goldLabelChoiceBox.currentTextChanged.connect(self.chooseGoldLabels)
        self.predLabelChoiceBox.currentTextChanged.connect(self.choosePredictions)

        vLayoutProperties.addStretch()

        self.computeBtn = QtWidgets.QPushButton("Analyze", self)
        vLayoutProperties.addWidget(self.computeBtn)
        self.computeBtn.clicked.connect(self.computePathwayAlignment)


        hLayoutFull.addLayout(vLayoutProperties, 1)

        # Pathways viewer

        vLayoutPlots = QtWidgets.QVBoxLayout()
        self.plotFigure = Figure()
        self.plotView = FigureCanvasQTAgg(self.plotFigure)

        self.plotToolbar = NavigationToolbar(self.plotView, self)

        self.plotScroll = QtWidgets.QScrollArea()
        self.plotView.resize(self.plotScroll.width(), 0)
        self.plotScroll.setWidget(self.plotView)

        #self.plotScene = QtWidgets.QGraphicsScene()
        #self.plotScene.addWidget(self.plotView)
        #self.plotGView = QtWidgets.QGraphicsView(self.plotScene)

        vLayoutPlots.addWidget(self.plotToolbar)
        vLayoutPlots.addWidget(self.plotScroll)
        hLayoutFull.addLayout(vLayoutPlots, 2)

        self.axes = None

    def computePathwayAlignment(self):
        p.compute_pathway_alignments()
        print(s.ATTRIBUTE_ALIGNMENT_SCORES)
        self._refreshPlots()

    def chooseGoldLabels(self):
        for a in s.ATTRIBUTE_CHECKLIST_STATE:
            if a == s.PRED_LABEL_ATTRIBUTE:
                continue
            s.ATTRIBUTE_CHECKLIST_STATE[a]['visible'] = True

        if self.goldLabelChoiceBox.currentText() in s.ATTRIBUTE_CHECKLIST_STATE:
            s.ATTRIBUTE_CHECKLIST_STATE[self.goldLabelChoiceBox.currentText()]['visible'] = False
        s.GOLD_LABEL_ATTRIBUTE = self.goldLabelChoiceBox.currentText()
        self._refreshAttributeList()
        self._refreshPlots()


    def choosePredictions(self):
        for a in s.ATTRIBUTE_CHECKLIST_STATE:
            if a == s.GOLD_LABEL_ATTRIBUTE:
                continue
            s.ATTRIBUTE_CHECKLIST_STATE[a]['visible'] = True

        if self.predLabelChoiceBox.currentText() in s.ATTRIBUTE_CHECKLIST_STATE:
            s.ATTRIBUTE_CHECKLIST_STATE[self.predLabelChoiceBox.currentText()]['visible'] = False
        s.PRED_LABEL_ATTRIBUTE = self.predLabelChoiceBox.currentText()
        self._refreshAttributeList()
        self._refreshPlots()

    def on_attribute_loaded(self):
        s.ATTRIBUTE_CHECKLIST_STATE = OrderedDict((a, {'checked': True,
                                                       'threshold': s.DEFAULT_PROBE_THRESHOLD,
                                                       'visible': True})
                                                  for a in s.ATTRIBUTE_MODEL.df.columns)



        self.goldLabelChoiceBox.clear()
        options = ['<None Selected>'] + [a for a in s.ATTRIBUTE_CHECKLIST_STATE]
        self.goldLabelChoiceBox.addItems(options)
        self.predLabelChoiceBox.clear()
        self.predLabelChoiceBox.addItems(options)

        self._refreshAttributeList()
        self._refreshPlots()

    def _refreshAttributeList(self):
        self.attributesListModel.clear()

        for attribute, state in s.ATTRIBUTE_CHECKLIST_STATE.items():
            if attribute == s.GOLD_LABEL_ATTRIBUTE or attribute == s.PRED_LABEL_ATTRIBUTE:
                continue
            list_item = QStandardItem(attribute)
            list_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            list_item.setData(Qt.Checked if state['checked'] else Qt.Unchecked, Qt.CheckStateRole)
            self.attributesListModel.appendRow((list_item, QStandardItem(str(state['threshold']))))

        self.attributesListModel.setHeaderData(0, Qt.Horizontal, "Attributes")
        self.attributesListModel.setHeaderData(1, Qt.Horizontal, "Threshold")

        self.attributesListView.repaint()

    def _refreshPlots(self):
        self.plotFigure.clear()
        self.plotFigure.suptitle("Attribute/Pathway Alignment")

        if s.PATHWAYS_MODEL is None:
            return

        x = list(range(s.PATHWAYS_MODEL.n_components_))
        #y = np.sin(x ** 2)  # TEST DATA
        # self.plotView.figure.set_figheight(20)

        visible_attributes = [a for a, state in s.ATTRIBUTE_CHECKLIST_STATE.items() if state['visible']]
        self.axes = self.plotView.figure.subplots(len(visible_attributes), sharex=True, sharey=True)

        for i, attribute in enumerate(visible_attributes):
            self.axes[i].clear()

            if i == 0:
                self.axes[i].xaxis.set_ticks_position('top')
            if i == len(visible_attributes)-1:
                self.axes[i].xaxis.set_ticks_position('bottom')

            self.axes[i].set_xticks(x, labels=['pathway_{}'.format(pw) for pw in x])

            self.axes[i].set_ylabel(attribute)

            if len(s.ATTRIBUTE_ALIGNMENT_CLFS) > 1:
                y = s.ATTRIBUTE_ALIGNMENT_CLFS[attribute].coef_[0]
            else:
                y = [0] * len(x)
            self.axes[i].bar(x, y, color=['blue' if np.abs(v) > s.ATTRIBUTE_CHECKLIST_STATE[attribute]['threshold']
                                          else 'grey' for v in y])
            self.axes[i].axhline(0, color='grey', linewidth=0.8)

        # self.plotScroll.setFrameRect((self.plotScroll.width(), 1000 * len(self.axes)))
        self.plotView.resize(self.plotView.get_width_height()[0], len(self.axes) * 200)
        self.plotView.draw()


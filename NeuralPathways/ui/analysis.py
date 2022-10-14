import numpy as np

from collections import OrderedDict
from functools import partial
from matplotlib.figure import Figure
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from qtpy import QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtGui import QStandardItemModel, QStandardItem, QFont

import NeuralPathways.session as s
import NeuralPathways.pathways as p

from NeuralPathways.utilities import NavigationToolbar, AlignmentDelegate


class AnalysisWidget(QtWidgets.QWidget):

    def __init__(self, bridge, parent=None):
        QtWidgets.QWidget.__init__(self, parent=None)

        sb = bridge
        sb.valueUpdated.connect(self.on_attribute_loaded)

        hLayoutFull = QtWidgets.QHBoxLayout(self)

        # Properties Sidebar
        vLayoutProperties = QtWidgets.QVBoxLayout()

        boldFont = QFont()
        boldFont.setBold(True)
        corrSectionLbl =QtWidgets.QLabel('Attribute Correlation:')
        corrSectionLbl.setFont(boldFont)

        attributes = s.ATTRIBUTE_MODEL.df.columns
        self.attributesListModel = QStandardItemModel(len(attributes), 4)
        self.attributesListModel.setHeaderData(0, Qt.Horizontal, "Attributes")
        self.attributesListModel.setHeaderData(1, Qt.Horizontal, "Threshold")
        self.attributesListModel.setHeaderData(2, Qt.Horizontal, "Corr. Class")
        self.attributesListModel.setHeaderData(3, Qt.Horizontal, "Display?")

        self.attributesListView = QtWidgets.QTreeView()
        self.attributesListView.setModel(self.attributesListModel)
        self.attributesListView.setAlternatingRowColors(True)

        # TODO: implement Pearson's r option
        self.corrMethodLbl = QtWidgets.QLabel("Correlation Method:")
        self.corrMethodChoiceBox = QtWidgets.QComboBox()
        self.corrMethodChoiceBox.addItems(['Logistic Regression', "Pearson's R Value"])
        self.corrMethodChoiceBox.setCurrentText("Pearson's R Value")

        self.dataColumnLbl = QtWidgets.QLabel("Data Column to Examine:")
        self.dataColumnChoiceBox = QtWidgets.QComboBox()
        self.dataColumnChoiceBox.addItems(['<None Selected>'])

        self.goldLabelLbl = QtWidgets.QLabel("Gold Label Column:")
        self.goldLabelChoiceBox = QtWidgets.QComboBox()
        self.goldLabelChoiceBox.addItems(['<None Selected>'])

        self.predLabelLbl = QtWidgets.QLabel("Model Predictions Column:")
        self.predLabelChoiceBox = QtWidgets.QComboBox()
        self.predLabelChoiceBox.addItems(['<None Selected>'])

        pathwayInspectorLbl = QtWidgets.QLabel("Pathway Data Inspector:")

        pathwayInspectorLbl.setFont(boldFont)
        self.pathwayChoiceLbl = QtWidgets.QLabel("Analyze pathways to enable inspector.")
        self.pathwaysDataInspectorListModel = QStandardItemModel(len(attributes), 3)
        self.pathwaysDataInspectorListModel.setHeaderData(0, Qt.Horizontal, "Data")
        self.pathwaysDataInspectorListModel.setHeaderData(1, Qt.Horizontal, "Attribute Label")
        self.pathwaysDataInspectorListModel.setHeaderData(2, Qt.Horizontal, "Pathway Activation")

        self.pathwaysDataInspectorListView = QtWidgets.QTreeView()
        self.pathwaysDataInspectorListView.setModel(self.pathwaysDataInspectorListModel)
        self.pathwaysDataInspectorListView.setAlternatingRowColors(True)

        hLayoutNInstances = QtWidgets.QHBoxLayout(self)
        self.topNInstancesSpinbox = QtWidgets.QSpinBox()
        self.topNInstancesSpinbox.setRange(1, 100)
        self.topNInstancesSpinbox.setValue(10)

        hLayoutNInstances.addWidget(QtWidgets.QLabel("Top N Instances:"))
        hLayoutNInstances.addWidget(self.topNInstancesSpinbox)

        hLayoutCorrMethod = QtWidgets.QHBoxLayout(self)
        hLayoutCorrMethod.addWidget(QtWidgets.QLabel('Method'), 1)
        hLayoutCorrMethod.addWidget(self.corrMethodChoiceBox, 4)

        vLayoutProperties.addWidget(corrSectionLbl)
        vLayoutProperties.addWidget(self.attributesListView)
        vLayoutProperties.addLayout(hLayoutCorrMethod)
        # vLayoutProperties.addWidget(self.goldLabelLbl)
        # vLayoutProperties.addWidget(self.goldLabelChoiceBox)
        # vLayoutProperties.addWidget(self.predLabelLbl)
        # vLayoutProperties.addWidget(self.predLabelChoiceBox)

        self.computeBtn = QtWidgets.QPushButton("Analyze", self)
        self.computeBtn.setFont(boldFont)
        vLayoutProperties.addWidget(self.computeBtn)
        self.computeBtn.clicked.connect(self.computePathwayAlignment)

        vLayoutProperties.addStretch()
        vLayoutProperties.addWidget(pathwayInspectorLbl)
        vLayoutProperties.addWidget(self.dataColumnLbl)
        vLayoutProperties.addWidget(self.dataColumnChoiceBox)
        vLayoutProperties.addLayout(hLayoutNInstances)
        vLayoutProperties.addWidget(self.pathwayChoiceLbl)
        vLayoutProperties.addWidget(self.pathwaysDataInspectorListView)

        self.dataColumnChoiceBox.currentTextChanged.connect(self.chooseDataColumn)
        self.goldLabelChoiceBox.currentTextChanged.connect(self.chooseGoldLabels)
        self.predLabelChoiceBox.currentTextChanged.connect(self.choosePredictions)

        hLayoutFull.addLayout(vLayoutProperties, 2)

        # Pathways viewer
        vLayoutPlots = QtWidgets.QVBoxLayout()
        self.plotFigure = Figure()
        self.plotView = FigureCanvasQTAgg(self.plotFigure)

        self.plotToolbar = NavigationToolbar(self.plotView, self)

        self.plotScroll = QtWidgets.QScrollArea()
        self.plotView.resize(self.plotScroll.width(), 0)
        self.plotScroll.setWidget(self.plotView)

        vLayoutPlots.addWidget(self.plotToolbar)
        vLayoutPlots.addWidget(self.plotScroll)
        hLayoutFull.addLayout(vLayoutPlots, 3)

        # self.plot = pg.MultiPlotWidget()
        #
        # y1 = [5, 5, 7, 10, 3, 8, 9, 1, 6, 2]
        # x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        # self.bargraph = pg.BarGraphItem(x=x, height=y1, width=0.6, brush='g')
        # self.plot.addItem(self.bargraph)
        #
        # hLayoutFull.addWidget(self.plot, 2)

        self.axes = None
        self.inspectionPathway = 0
        self.inspectionAttribute = None
        self.lastColor = None
        self.lastSelectedBox = None

    def computePathwayAlignment(self):
        method = p.CorrelationMethod.PEARSON

        if self.corrMethodChoiceBox.currentText() == "Logistic Regression":
            method = p.CorrelationMethod.LOG_REG

        p.compute_pathway_alignments(method=method)
        #print(s.ATTRIBUTE_ALIGNMENT_SCORES)
        self._refreshPlots()

    def chooseDataColumn(self):
        for a in s.ATTRIBUTE_CHECKLIST_STATE:
            if a == s.PRED_LABEL_ATTRIBUTE:
                continue
            s.ATTRIBUTE_CHECKLIST_STATE[a]['visible'] = True

        if self.dataColumnChoiceBox.currentText() in s.ATTRIBUTE_CHECKLIST_STATE:
            s.ATTRIBUTE_CHECKLIST_STATE[self.dataColumnChoiceBox.currentText()]['visible'] = False
        s.DATA_COLUMN_ATTRIBUTE = self.dataColumnChoiceBox.currentText()
        self._refreshAttributeList()
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

    def on_attribute_chk_toggle(self, state, chk_box):
        print(state, chk_box.PATHWAYS_attribute)
        s.ATTRIBUTE_CHECKLIST_STATE[chk_box.PATHWAYS_attribute]['checked'] = bool(state)
        self._refreshPlots()
    def on_corr_class_select(self, cbox):
        print(cbox.currentText(), cbox.PATHWAYS_attribute)
        s.ATTRIBUTE_CHECKLIST_STATE[cbox.PATHWAYS_attribute]['corr_class'] = cbox.currentText()

    def on_attribute_loaded(self):
        print("Attributes Loaded")

        s.ATTRIBUTE_CHECKLIST_STATE = OrderedDict((a, {'checked': True,
                                                       'threshold': s.DEFAULT_PROBE_THRESHOLD,
                                                       'visible': True})
                                                  for a in s.ATTRIBUTE_MODEL.df.columns)

        # Get class values ()
        for a in s.ATTRIBUTE_MODEL.df.columns:
            classes = sorted(s.ATTRIBUTE_MODEL.df[a].unique())
            if len(classes) > 50 or len(classes) <= 1:
                s.ATTRIBUTE_CHECKLIST_STATE[a]['classes'] = ['n/a']
                s.ATTRIBUTE_CHECKLIST_STATE[a]['checked'] = False
            else:
                s.ATTRIBUTE_CHECKLIST_STATE[a]['classes'] = classes

            if len(classes) == 2 and any([str(classes[0]) == "0" and str(classes[1]) == "1",
                                         str(classes[0]).lower() == 'false' and str(classes[1]).lower() == 'true',
                                         str(classes[0]).lower() == 'n' and str(classes[1]).lower() == 'y',
                                         str(classes[0]).lower() == 'no' and str(classes[1]).lower() == 'yes']):
                s.ATTRIBUTE_CHECKLIST_STATE[a]['corr_class'] = s.ATTRIBUTE_CHECKLIST_STATE[a]['classes'][1]
            else:
                s.ATTRIBUTE_CHECKLIST_STATE[a]['corr_class'] = s.ATTRIBUTE_CHECKLIST_STATE[a]['classes'][0]

        self.dataColumnChoiceBox.clear()
        self.goldLabelChoiceBox.clear()
        self.predLabelChoiceBox.clear()

        options = ['<None Selected>'] + [a for a in s.ATTRIBUTE_CHECKLIST_STATE]
        self.dataColumnChoiceBox.addItems(options)
        self.goldLabelChoiceBox.addItems(options)
        self.predLabelChoiceBox.addItems(options)

        self._refreshAttributeList()
        self._refreshPlots()

    def _refreshAttributeList(self):
        self.attributesListModel.clear()

        for attribute, state in s.ATTRIBUTE_CHECKLIST_STATE.items():
            if attribute == s.GOLD_LABEL_ATTRIBUTE or attribute == s.PRED_LABEL_ATTRIBUTE:
                continue
            list_item = QStandardItem(attribute)
            #list_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            #list_item.setData(Qt.Checked if state['checked'] else Qt.Unchecked, Qt.CheckStateRole)

            # Set up check mark
            display_item = QStandardItem()
            display_checkbox = QtWidgets.QCheckBox()
            display_checkbox.setChecked(s.ATTRIBUTE_CHECKLIST_STATE[attribute]['checked'])
            display_checkbox.stateChanged.connect(partial(self.on_attribute_chk_toggle,
                                                          chk_box=display_checkbox))

            display_checkbox.PATHWAYS_attribute = attribute

            # Set up choice for which class to correlate with
            corr_class_item = QStandardItem()
            corr_class_cbox = QtWidgets.QComboBox()
            corr_class_cbox.addItems([str(cls) for cls in state['classes']])
            corr_class_cbox.setCurrentText(str(state['corr_class']))
            corr_class_cbox.currentTextChanged.connect(partial(self.on_corr_class_select,
                                                               cbox=corr_class_cbox))
            corr_class_cbox.PATHWAYS_attribute = attribute

            self.attributesListModel.appendRow((list_item,
                                                QStandardItem(str(state['threshold'])),
                                                corr_class_item,
                                                display_item))

            # Register inline widgets
            self.attributesListView.setIndexWidget(corr_class_item.index(), corr_class_cbox)
            self.attributesListView.setIndexWidget(display_item.index(), display_checkbox)

        self.attributesListModel.setHeaderData(0, Qt.Horizontal, "Attributes")
        self.attributesListModel.setHeaderData(1, Qt.Horizontal, "Threshold")
        self.attributesListModel.setHeaderData(2, Qt.Horizontal, "Corr. Class")
        self.attributesListModel.setHeaderData(3, Qt.Horizontal, "Display?")

        # # Center Display column (NOT WORKING)
        # delegate = AlignmentDelegate(self.attributesListView)
        # self.attributesListView.setItemDelegate(delegate)
        # delegate.set_column_alignment(3, Qt.AlignCenter)

        self.attributesListView.repaint()

    def _refreshDataInspectorList(self):
        self.pathwaysDataInspectorListModel.clear()

        pathway_activations = s.PATHWAYS_ACTIVATIONS[:, self.inspectionPathway]
        # print(pathway_activations)
        attribute_values = list(s.ATTRIBUTE_MODEL.df[self.inspectionAttribute])
        # print(attribute_values)
        data_column = self.dataColumnChoiceBox.currentText()
        # print(data_column)

        n = self.topNInstancesSpinbox.value()
        ind = np.argpartition(pathway_activations, -n)[-n:]
        top_n_idxs = ind[np.argsort(pathway_activations[ind])][::-1]
        data_values = list(s.ATTRIBUTE_MODEL.df[data_column][top_n_idxs])

        for idx, d in zip(top_n_idxs, data_values):
            self.pathwaysDataInspectorListModel.appendRow((QStandardItem(str(d)),
                                                           QStandardItem(str(attribute_values[idx])),
                                                           QStandardItem(f"{pathway_activations[idx]:.03f}")))

        self.pathwaysDataInspectorListModel.setHeaderData(0, Qt.Horizontal, "Data")
        self.pathwaysDataInspectorListModel.setHeaderData(1, Qt.Horizontal, "Attribute Label")
        self.pathwaysDataInspectorListModel.setHeaderData(2, Qt.Horizontal, "Pathway Activation")

        self.pathwaysDataInspectorListView.repaint()

    # def _refreshPlots(self):
    #     pass

    def _refreshPlots(self):
        self.plotFigure.clear()
        self.plotFigure.suptitle("Attribute/Pathway Alignment")

        self.lastColor = None
        self.lastSelectedBox = None
        self.pathwaysDataInspectorListModel.clear()
        self.pathwaysDataInspectorListView.repaint()

        if s.PATHWAYS_MODEL is None:
            return

        self.inspectionPathway = 0
        self.inspectionAttribute = None
        self.pathwayChoiceLbl.setText("Click on a bar to inspect the data that most activates the pathways.")

        x = list(range(s.PATHWAYS_MODEL.n_components_))
        #y = np.sin(x ** 2)  # TEST DATA
        # self.plotView.figure.set_figheight(20)

        visible_attributes = [a for a, state in s.ATTRIBUTE_CHECKLIST_STATE.items()
                              if state['visible'] and state['checked']]
        self.axes = self.plotView.figure.subplots(len(visible_attributes), sharex=True, sharey=True)

        if not isinstance(self.axes, np.ndarray):
            self.axes = [self.axes]

        for i, attribute in enumerate(visible_attributes):
            self.axes[i].clear()

            if i == 0:
                self.axes[i].xaxis.set_ticks_position('top')
                self.axes[i].set_xticks(x,
                                        labels=['pathway_{}'.format(pw) for pw in x],
                                        rotation=60,
                                        ha='left')
            elif i == len(visible_attributes)-1:
                self.axes[i].xaxis.set_ticks_position('bottom')
                self.axes[i].set_xticks(x,
                                        labels=['pathway_{}'.format(pw) for pw in x],
                                        rotation=60,
                                        ha='right')
            else:
                self.axes[i].set_xticks(x, labels=['pathway_{}'.format(pw) for pw in x])

            self.axes[i].set_ylabel(attribute)

            target = s.ATTRIBUTE_CHECKLIST_STATE[attribute]['corr_class']

            if len(s.ATTRIBUTE_ALIGNMENT_CLFS) >= 1 and \
                    s.ATTRIBUTE_ALIGNMENT_CLFS[attribute].coef_.shape[0] > 1 and \
                    target != "n/a":
                idx = list(s.ATTRIBUTE_ALIGNMENT_CLFS[attribute].classes_).index(target)
                y = s.ATTRIBUTE_ALIGNMENT_CLFS[attribute].coef_[idx]
            elif len(s.ATTRIBUTE_ALIGNMENT_CLFS) >= 1 and \
                    s.ATTRIBUTE_ALIGNMENT_CLFS[attribute].coef_.shape[0] == 1 and \
                    target != "n/a":
                y = s.ATTRIBUTE_ALIGNMENT_CLFS[attribute].coef_[0]
            else:
                print('n/a')
                y = [0] * len(x)
            self.axes[i].bar(x, y,
                             color=['blue' if np.abs(v) > s.ATTRIBUTE_CHECKLIST_STATE[attribute]['threshold']
                                          else 'grey' for v in y],
                             picker=True)
            self.axes[i].axhline(0, color='grey', linewidth=0.8)
            self.axes[i].figure.canvas.mpl_connect('pick_event', self.on_bar_select)

        # self.plotScroll.setFrameRect((self.plotScroll.width(), 1000 * len(self.axes)))
        self.plotView.resize(self.plotView.get_width_height()[0], 500 + len(self.axes) * 200)
        self.plotView.draw()

    def on_bar_select(self, event):

        if event.mouseevent.button is MouseButton.LEFT:
            if self.dataColumnChoiceBox.currentText() == '<None Selected>':
                self.pathwayChoiceLbl.setText(f'Please select a data column.')
                return

            ax = event.mouseevent.inaxes
            attribute = ax.get_ylabel()

            bar = event.artist
            x = bar.get_x()
            idx = int(x.round())

            if self.lastSelectedBox:
                self.lastSelectedBox.set_facecolor(self.lastColor)

            self.lastColor = bar.get_facecolor()
            self.lastSelectedBox = bar
            bar.set_facecolor('red')

            self.inspectionPathway = idx
            self.inspectionAttribute = attribute
            self.pathwayChoiceLbl.setText(f'Inspecting Pathway {idx} with attribute, "{attribute}"')

            self._refreshDataInspectorList()
            self.plotView.draw()

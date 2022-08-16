import json
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import qtpynodeeditor as ne

from collections import OrderedDict
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from qtpy import QtWidgets
from qtpy.compat import getsavefilename
from qtpy.QtCore import Qt
from qtpy.QtGui import QStandardItemModel, QStandardItem

from qtpy.QtWidgets import QTreeView, QHeaderView
from qtpynodeeditor import Port, PortType
from qtpynodeeditor.type_converter import TypeConverter

import NeuralPathways.session as s
import NeuralPathways.pathways as p

from NeuralPathways.models.node_model import (VariableData, VariableListData, variable_to_variable_list_converter,
                                              InitializerDataModel, ObservedExogenousVariableModel,
                                              BinomialExogenousVariableModel,
                                              VariableInputNodeModel, EndogenousVariableDataModel,
                                              TabularEndogenousVariableDataModel)
from NeuralPathways.utilities import NavigationToolbar


class CausalityWidget(QtWidgets.QWidget):

    def __init__(self, bridge, parent=None):
        QtWidgets.QWidget.__init__(self, parent=None)

        sb = bridge
        #sb.valueUpdated.connect(self.on_attribute_loaded)

        hLayoutFull = QtWidgets.QHBoxLayout(self)

        # Properties Sidebar
        vLayoutProperties = QtWidgets.QVBoxLayout()

        # Graph dispaly image

        vLayoutPlots = QtWidgets.QVBoxLayout()
        self.plotFigure = plt.figure() #Figure()
        self.plotView = FigureCanvasQTAgg(self.plotFigure)
        self.plotToolbar = NavigationToolbar(self.plotView, self)

        vLayoutPlots.addWidget(self.plotToolbar)
        vLayoutPlots.addWidget(self.plotView)

        # Generated Data Display

        #self.generatedDataTable = QtWidgets.QTableView()
        generatedData = s.CAUSAL_GENERATED_DATA.df.columns
        self.generatedDataModel = QStandardItemModel(1, 1)
        self.generatedDataModel.setHeaderData(0, Qt.Horizontal, "Variables")

        self.generatedDataView = QtWidgets.QTreeView()
        self.generatedDataView.setModel(self.generatedDataModel)
        self.generatedDataView.setAlternatingRowColors(True)


        hLayoutNumData = QtWidgets.QHBoxLayout()
        self.numDataToGenerateChoice = QtWidgets.QSpinBox()
        self.numDataToGenerateChoice.setMaximum(10000)
        self.numDataToGenerateChoice.setMinimum(100)
        self.numDataToGenerateChoice.setSingleStep(100)
        self.numDataToGenerateChoice.setValue(1000)

        hLayoutNumData.addWidget(QtWidgets.QLabel("# of Data to Generate:"))
        hLayoutNumData.addWidget(self.numDataToGenerateChoice)

        self.generateBtn = QtWidgets.QPushButton("Generate", self)
        self.saveBtn = QtWidgets.QPushButton("Save", self)
        self.saveBtn.clicked.connect(self._save_generated_data)

        vLayoutProperties.addLayout(vLayoutPlots)
        vLayoutProperties.addWidget(QtWidgets.QLabel("Generated Data:"))
        vLayoutProperties.addWidget(self.generatedDataView)
        vLayoutProperties.addLayout(hLayoutNumData)
        vLayoutProperties.addWidget(self.generateBtn)
        vLayoutProperties.addWidget(self.saveBtn)
        #vLayoutProperties.addLayout(hLayoutSaveFile)
        vLayoutProperties.addStretch()

        self.generateBtn.clicked.connect(self._compute_graph)

        # Node Editor
        registry = ne.DataModelRegistry()

        registry.register_model(InitializerDataModel, category='Internal',
                                style=None)

        models = (ObservedExogenousVariableModel, BinomialExogenousVariableModel)
        for model in models:
            registry.register_model(model, category='Exogenous Variables',
                                    style=None)

        models = (TabularEndogenousVariableDataModel,)
        for model in models:
            registry.register_model(model, category='Endogenous Variables',
                                    style=None)

        #registry.register_model(VariableInputNodeModel, category='Internal',
        #                        style=None)
        #registry.register_model(EndogenousVariableDataModel, category='Internal',
        #                        style=None)

        # Register converter from single variables to singleton lists of variables
        var_converter = TypeConverter(VariableData.data_type, VariableListData.data_type,
                                      variable_to_variable_list_converter)
        registry.register_type_converter(VariableData.data_type, VariableListData.data_type, var_converter)



        scene = ne.FlowScene(registry=registry)

        view = ne.FlowView(scene)
        #view.setWindowTitle("Calculator example")
        #view.resize(800, 600)
        #view.show()

        hLayoutFull.addWidget(view, 2)
        hLayoutFull.addLayout(vLayoutProperties, 1)

        node_init = scene.create_node(InitializerDataModel)



        #try:
        #    scene.auto_arrange(nodes=[node_init], layout='bipartite')
        #except ImportError:
        #    ...

        """
        inputs = []
        node_add = scene.create_node(AdditionModel)
        node_sub = scene.create_node(SubtractionModel)
        node_mul = scene.create_node(MultiplicationModel)
        node_div = scene.create_node(DivisionModel)
        node_mod = scene.create_node(ModuloModel)

        for node_operation in (node_add, node_sub, node_mul, node_div, node_mod):
            node_a = scene.create_node(NumberSourceDataModel)
            node_a.model.embedded_widget().setText('1.0')
            inputs.append(node_a)

            node_b = scene.create_node(NumberSourceDataModel)
            node_b.model.embedded_widget().setText('2.0')
            inputs.append(node_b)

            scene.create_connection(node_a[PortType.output][0],
                                    node_operation[PortType.input][0],
                                    )

            scene.create_connection(node_b[PortType.output][0],
                                    node_operation[PortType.input][1],
                                    )

            node_display = scene.create_node(NumberDisplayModel)

            scene.create_connection(node_operation[PortType.output][0],
                                    node_display[PortType.input][0],
                                    )

        try:
            scene.auto_arrange(nodes=inputs, layout='bipartite')
        except ImportError:
            ...
        """

    def _compute_graph(self):
        # Draw graph
        self.plotFigure.clf()
        s.CAUSAL_GRAPH_INITIALIZER.reset()
        nx_graph = nx.DiGraph(s.CAUSAL_GRAPH_DEFINITION.edges())
        nx.draw_networkx(nx_graph, with_labels=True)
        self.plotView.draw_idle()

        # Generate Data
        generated_df = s.CAUSAL_GRAPH_DEFINITION.simulate(n_samples=self.numDataToGenerateChoice.value())
        generated_df = generated_df.reindex(sorted(generated_df.columns), axis=1)
        s.CAUSAL_GENERATED_DATA.updateDataframe(generated_df)
        print(generated_df)
        self._display_generated_data()

    def _display_generated_data(self):
        print(s.CAUSAL_GENERATED_DATA.columnCount(), s.CAUSAL_GENERATED_DATA.rowCount())
        self.generatedDataModel = QStandardItemModel(s.CAUSAL_GENERATED_DATA.rowCount(),
                                                     s.CAUSAL_GENERATED_DATA.columnCount())
        self.generatedDataModel.clear()

        for i, row in s.CAUSAL_GENERATED_DATA.df.iterrows():
            self.generatedDataModel.appendRow(tuple([QStandardItem(f"{n}") for n in row]))

        for i, node in enumerate(sorted(s.CAUSAL_GENERATED_DATA.df.columns)):
            self.generatedDataModel.setHeaderData(i, Qt.Horizontal, node)

        self.generatedDataView.setModel(self.generatedDataModel)

    def _save_generated_data(self):
        fname, _ = getsavefilename(self, 'Save File', filters="Comma Separated Values (*.csv)")
        s.CAUSAL_GENERATED_DATA.df.to_csv(fname, index=False)

    def _test_button(self):
        print('Testing button - this should generate a graph image')
        self.plotFigure.clf()

        B = nx.Graph()
        B.add_nodes_from([1, 2, 3, 4], bipartite=0)
        B.add_nodes_from(['a', 'b', 'c', 'd', 'e'], bipartite=1)
        B.add_edges_from([(1, 'a'), (2, 'c'), (3, 'd'), (3, 'e'), (4, 'e'), (4, 'd')])

        X = set(n for n, d in B.nodes(data=True) if d['bipartite'] == 0)
        Y = set(B) - X

        X = sorted(X, reverse=True)
        Y = sorted(Y, reverse=True)

        pos = dict()
        pos.update((n, (1, i)) for i, n in enumerate(X))  # put nodes from X at x=1
        pos.update((n, (2, i)) for i, n in enumerate(Y))  # put nodes from Y at x=2
        nx.draw_networkx(B, pos=pos, with_labels=True)

        print(B)

        self.plotView.draw_idle()

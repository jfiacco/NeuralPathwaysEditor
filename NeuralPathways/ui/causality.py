import json
import qtpynodeeditor as ne
import numpy as np

from collections import OrderedDict
from qtpy import QtWidgets
from qtpy.QtCore import Qt
from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtWidgets import QTreeView, QHeaderView
from qtpynodeeditor import Port, PortType
from qtpynodeeditor.type_converter import TypeConverter

import NeuralPathways.session as s
import NeuralPathways.pathways as p

from NeuralPathways.models.node_model import (VariableData, VariableListData, variable_to_variable_list_converter,
                                              InitializerDataModel, ObservedExogenousVariableModel,
                                              VariableInputNodeModel, EndogenousVariableDataModel, TabularEndogenousVariableDataModel)
from NeuralPathways.utilities import NavigationToolbar

class CausalityWidget(QtWidgets.QWidget):

    def __init__(self, bridge, parent=None):
        QtWidgets.QWidget.__init__(self, parent=None)

        sb = bridge
        #sb.valueUpdated.connect(self.on_attribute_loaded)

        hLayoutFull = QtWidgets.QHBoxLayout(self)

        # Properties Sidebar
        vLayoutProperties = QtWidgets.QVBoxLayout()

        registry = ne.DataModelRegistry()

        registry.register_model(InitializerDataModel, category='Internal',
                                style=None)

        models = (ObservedExogenousVariableModel,)
        for model in models:
            registry.register_model(model, category='Exogenous Variables',
                                    style=None)

        models = (TabularEndogenousVariableDataModel,)
        for model in models:
            registry.register_model(model, category='Endogenous Variables',
                                    style=None)

        registry.register_model(VariableInputNodeModel, category='Internal',
                                style=None)
        registry.register_model(EndogenousVariableDataModel, category='Internal',
                                style=None)

        # Register converter from single variables to singleton lists of variables
        var_converter = TypeConverter(VariableData.data_type, VariableListData.data_type,
                                      variable_to_variable_list_converter)
        registry.register_type_converter(VariableData.data_type, VariableListData.data_type, var_converter)



        scene = ne.FlowScene(registry=registry)

        view = ne.FlowView(scene)
        #view.setWindowTitle("Calculator example")
        #view.resize(800, 600)
        #view.show()

        hLayoutFull.addWidget(view)

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

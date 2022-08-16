import contextlib
import logging
import threading
import itertools

import numpy as np

from abc import ABC, abstractmethod
from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete.CPD import TabularCPD

from qtpy import QtWidgets
from qtpy.QtCore import Signal, Qt
from qtpy.QtGui import QIntValidator, QDoubleValidator, QStandardItem, QStandardItemModel

import qtpynodeeditor as nodeeditor

from qtpynodeeditor import (NodeData, NodeDataModel, NodeDataType,
                            NodeValidationState, Port, PortType)

import NeuralPathways.session as s


class VariableListData(NodeData):
    data_type = NodeDataType("variable_list", "VariableList")

    def __init__(self, variables=[]):
        self._vars = variables
        self._lock = threading.RLock()

    @property
    def lock(self):
        return self._lock

    @property
    def variables(self) -> list:
        return self._vars

    def variables_as_text(self) -> str:
        return '[' + ', '.join([v.variable_name() for v in self._vars]) + ']'


class VariableData(NodeData):
    data_type = NodeDataType("variable", "Variable")

    def __init__(self, variable_id: str = 'x', variable_name: str = 'X', discrete_values=2):
        self._var_id = variable_id
        self._var_name = variable_name
        self._discrete_values = discrete_values
        self._lock = threading.RLock()

    @property
    def lock(self):
        return self._lock

    @property
    def variable_name(self) -> str:
        return self._var_name

    @property
    def variable_id(self) -> str:
        return self._var_id

    @property
    def discrete_values(self) -> int:
        return self._discrete_values


class InitializerData(NodeData):
    data_type = NodeDataType("initialize", "Initialize")

    def __init__(self, initializer):
        self._lock = threading.RLock()

    @property
    def lock(self):
        return self._lock


def variable_to_variable_list_converter(data: VariableData) -> VariableListData:
    return VariableListData([data])


class InitializerDataModel(NodeDataModel):
    caption_visible = True
    num_ports = {
        'input': 0,
        'output': 1,
    }
    port_caption_visible = True
    data_type = {
        PortType.output: {
            0: InitializerData.data_type
        },
    }

    name = "Initializer"
    port_caption = {'output': {0: 'Exogenous Variables'}}

    instance = None

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)

        self._result = None

        if InitializerDataModel.instance is None:
            InitializerDataModel.instance = self
            s.CAUSAL_GRAPH_INITIALIZER = self
            self._validation_state = NodeValidationState.valid
            self._validation_message = ''
            self.compute()
        else:
            self._validation_state = NodeValidationState.error
            self._validation_message = "Only one initializer allowed. DELETE this node."
            self.data_invalidated.emit(0)

    def validation_state(self) -> NodeValidationState:
        return self._validation_state

    def validation_message(self) -> str:
        return self._validation_message

    def out_data(self, port: int) -> NodeData:
        return self._result

    def compute(self):
        print("INITIALIZER NODE COMPUTE")
        if s.CAUSAL_GRAPH_DEFINITION is not None:
            print("OVERWRITING EXISTING GRAPH")
        s.CAUSAL_GRAPH_DEFINITION = BayesianNetwork()
        self._result = InitializerData(self.instance)

    def mark_stale(self):
        self._validation_state = NodeValidationState.error
        self._validation_message = "Graph has changed. Re-generate graph."
        self.data_invalidated.emit(0)

    def reset(self):
        print("INITIALIZER RESET")
        self.compute()
        self._validation_state = NodeValidationState.valid
        self._validation_message = 'Graph refreshed.'
        self.data_updated.emit(0)


class ExogenousVariableDataModel(NodeDataModel):
    caption_visible = True
    num_ports = {
        'input': 1,
        'output': 1,
    }
    port_caption = {
        'input': {0: 'Initializer'},
        'output': {0: 'Out'}
    }
    port_caption_visible = True
    data_type = {
        PortType.input: {
            0: InitializerData.data_type,
        },
        PortType.output: {
            0: VariableData.data_type,
        },
    }

    num_instances = 0

    class ExoNodeWidget(QtWidgets.QWidget):

        def __init__(self, parent=None):
            QtWidgets.QWidget.__init__(self, parent=None)

            self.node_layout = QtWidgets.QVBoxLayout()
            self.setLayout(self.node_layout)

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)

        self._var_id = None
        self._var_name = None
        self._result = None
        self._validation_state = NodeValidationState.warning
        self._validation_message = 'Uninitialized'

        self.main_widget = self.ExoNodeWidget()

        self._var_name = str(self.name) + f'_{type(self).num_instances}'
        self._var_id = self._var_name.lower()

        type(self).num_instances += 1

        self.node_label = QtWidgets.QLineEdit(self._var_name)
        self.main_widget.node_layout.addWidget(self.node_label)
        self.node_label.textChanged.connect(self.on_node_label_changed)

        self._parents = {}

    @property
    def caption(self):
        return self.name

    def on_node_label_changed(self):
        # TODO Ensure that node id is unique
        self._var_name = self.node_label.text()
        s.CAUSAL_GRAPH_INITIALIZER.mark_stale()
        self.data_updated.emit(0)

    def set_in_data(self, data: NodeData, port: Port):
        """
        This node was connected to an initializer node
        Parameters
        ----------
        data : NodeData
        port : Port
        """

        self._parents[port.index] = data

        if self._check_inputs():
            print("INPUTS CHECK OUT")
            with self._compute_lock():
                print("COMPUTING")
                self.compute()
        else:
            s.CAUSAL_GRAPH_INITIALIZER.mark_stale()

    def _check_inputs(self):
        """
        Validate that the initializer is valid
        :return:
        """

        # Check initializer
        if s.CAUSAL_GRAPH_DEFINITION is None:
            return False

        # Remove stale parents
        for k in list(self._parents.keys()):
            if k not in self.data_type[PortType.input]:
                self._parents.pop(k)

        parents_ok = {}

        # Determine if each input is both connected and the correct type
        for p_idx, p_type in self.data_type[PortType.input].items():
            parents_ok[p_idx] = (p_idx in self._parents and
                                 self._parents[p_idx] is not None and
                                 self._parents[p_idx].data_type.id in ('initialize',))

        print(self._parents)
        print(parents_ok)

        # If ANY of the inputs are unconnected or typed incorrectly, give the user a warning
        if not all(parents_ok.values()):
            self._validation_state = NodeValidationState.warning
            self._validation_message = "Missing or incorrect inputs"
            self._result = None
            self.data_updated.emit(0)
            return False

        # Otherwise, the node is valid
        self._validation_state = NodeValidationState.valid
        self._validation_message = ''
        self.data_updated.emit(0)
        return True

    @contextlib.contextmanager
    def _compute_lock(self):

        # Check if inputs are not set
        parents_ok = {}
        for p_idx, p_type in self.data_type[PortType.input].items():
            parents_ok[p_idx] = (p_idx in self._parents and
                                 self._parents[p_idx] is not None)

        if not all(parents_ok.values()):
            raise RuntimeError('Inputs not set.')

        # Set all the locks (make sure that we properly release the lock if we cannot use 'with' statements)
        with contextlib.ExitStack() as stack:
            locks = [stack.enter_context(self._parents[p_idx].lock)
                     for p_idx in self.data_type[PortType.input].keys()]
            yield

        # Mark that the data has been updated
        self.data_updated.emit(0)

    def out_data(self, port: int) -> NodeData:
        return self._result

    def validation_state(self) -> NodeValidationState:
        return self._validation_state

    def validation_message(self) -> str:
        return self._validation_message

    def save(self) -> dict:
        """Add to the JSON dictionary to save the state of the NumberSource"""
        doc = super().save()
        if self._validation_state == NodeValidationState.valid:
            doc['variable_id'] = self._var_id
            doc['variable_name'] = self._var_name
        return doc

    def restore(self, state: dict):
        """Restore the number from the JSON dictionary"""
        try:
            self._var_id = state["variable_id"]
            self._var_name = state["variable_name"]
        except Exception:
            ...
        else:
            self._result = VariableData(self._var_id, self._var_name)

    def embedded_widget(self) -> QtWidgets.QWidget:
        return self.main_widget

    def compute(self):
        print("THIS SHOULD NOT BE COMPUTED")
        ...


class BinomialExogenousVariableModel(ExogenousVariableDataModel):
    name = "Binomial"

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)

        self._probability_choice = QtWidgets.QDoubleSpinBox()
        self._probability_choice.setMaximum(1.0)
        self._probability_choice.setMinimum(0.0)
        self._probability_choice.setSingleStep(0.1)
        self._probability_choice.setValue(0.5)

        self.main_widget.node_layout.addWidget(self._probability_choice)

        self._probability_choice.valueChanged.connect(self.on_probability_changed)

    def on_probability_changed(self):
        s.CAUSAL_GRAPH_INITIALIZER.mark_stale()
        self.data_updated.emit(0)

    def compute(self):
        print("BINOMIAL NODE COMPUTE")
        if s.CAUSAL_GRAPH_DEFINITION is None:
            self._validation_state = NodeValidationState.error
            self._validation_message = 'No root causal graph. (Graph may be uninitialized)'
            self._result = None
            return

        s.CAUSAL_GRAPH_DEFINITION.add_node(self._var_name)

        p = self._probability_choice.value()
        cpd_table = TabularCPD(self._var_name, 2, [[1-p], [p]])
        s.CAUSAL_GRAPH_DEFINITION.add_cpds(cpd_table)

        print(s.CAUSAL_GRAPH_DEFINITION)

        self._validation_state = NodeValidationState.valid
        self._validation_message = ''
        self._result = VariableData(self._var_id, self._var_name)

    def save(self) -> dict:
        """Add to the JSON dictionary to save the state of the NumberSource"""
        doc = super().save()
        if self._validation_state == NodeValidationState.valid:
            doc['probability'] = self._probability_choice.value()
        return doc

    def restore(self, state: dict):
        """Restore the number from the JSON dictionary"""
        try:
            p = state["probability"]
        except Exception:
            ...
        else:
            # TODO: Check to make sure attribute is valid
            self._probability_choice.setValue(p)


class ObservedExogenousVariableModel(ExogenousVariableDataModel):
    name = "Observed"

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)

        self._attribute_choice = QtWidgets.QComboBox()
        self._attribute_choice.addItems(['<None Selected>'])
        self._attribute_choice.addItems([a for a in s.ATTRIBUTE_CHECKLIST_STATE])
        self._attribute_choice.currentTextChanged.connect(self.on_choice)
        s.sig_attribute_loaded.valueUpdated.connect(self.on_attribute_load)

        self.main_widget.node_layout.addWidget(self._attribute_choice)

    def compute(self):
        if self._attribute_choice.currentText() == '<None Selected>':
            self._validation_state = NodeValidationState.error
            self._validation_message = "Node must link to an attribute."
            self._result = None
        else:
            print('result set')
            self._validation_state = NodeValidationState.valid
            self._validation_message = ''
            self._result = VariableData(self._var_id, self._var_name)

    def save(self) -> dict:
        """Add to the JSON dictionary to save the state of the NumberSource"""
        doc = super().save()
        if self._validation_state == NodeValidationState.valid:
            doc['attribute'] = self._attribute_choice.currentText()
        return doc

    def restore(self, state: dict):
        """Restore the number from the JSON dictionary"""
        try:
            attribute = state["attribute"]
        except Exception:
            ...
        else:
            # TODO: Check to make sure attribute is valid
            self._attribute_choice.setCurrentText(attribute)

    def on_choice(self, string: str):
        attribute = self._attribute_choice.currentText()

        if attribute == '<None Selected>':
            self._validation_state = NodeValidationState.warning
            self._validation_message = "No attribute selected"
            self._result = None
            self.data_invalidated.emit(0)
            self.data_updated.emit(0)
        else:
            self.compute()
            self.data_updated.emit(0)

    def on_attribute_load(self):
        options = ['<None Selected>'] + [a for a in s.ATTRIBUTE_CHECKLIST_STATE]
        self._attribute_choice.clear()
        self._attribute_choice.addItems(options)


class VariableInputNodeModel(NodeDataModel):
    caption_visible = True
    num_ports = {
        'input': 1,
        'output': 1,
    }
    port_caption = {
        'input': {0: 'a'},
        'output': {0: 'Out'}
    }
    port_caption_visible = True
    data_type = {
        PortType.input: {
            0: VariableData.data_type,
        },
        PortType.output: {
            0: VariableData.data_type,
        },
    }
    ports_updated = Signal(int)
    max_inputs = 5

    class MultiNodeWidget(QtWidgets.QWidget):

        def __init__(self, parent=None):
            QtWidgets.QWidget.__init__(self, parent=None)

            self.node_layout = QtWidgets.QVBoxLayout()
            self.setLayout(self.node_layout)

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)

        self._num_inputs = 1
        self._base_class = type(self)

        self.main_widget = self.MultiNodeWidget()

        self._add_remove_layout = QtWidgets.QHBoxLayout()
        self._add_button = QtWidgets.QPushButton('+')
        self._add_button.setMaximumWidth(self._add_button.height() / 15)
        self._add_button.setContentsMargins(0, 0, 0, 0)
        self._remove_button = QtWidgets.QPushButton('-')
        self._remove_button.setMaximumWidth(self._remove_button.height() / 15)
        self._remove_button.setContentsMargins(0, 0, 0, 0)
        self._add_remove_label = QtWidgets.QLabel('Add/Remove Parents:')
        self._add_remove_label.setContentsMargins(0, 0, 10, 0)

        self._add_remove_layout.setSpacing(0)
        self._add_remove_layout.addWidget(self._add_remove_label)
        self._add_remove_layout.addStretch()
        self._add_remove_layout.addWidget(self._add_button)
        self._add_remove_layout.addWidget(self._remove_button)

        self.main_widget.node_layout.addLayout(self._add_remove_layout)

        self._add_button.clicked.connect(self._on_add_input)
        self._remove_button.clicked.connect(self._on_remove_input)

    def embedded_widget(self) -> QtWidgets.QWidget:
        return self.main_widget

    def _on_add_input(self):
        self._add_button.setDisabled(True)
        self._remove_button.setDisabled(True)

        if self._num_inputs < self.max_inputs:
            self._num_inputs += 1
            self._update_inputs()

        self._add_button.setDisabled(False)
        self._remove_button.setDisabled(False)

    def _on_remove_input(self):
        self._add_button.setDisabled(True)
        self._remove_button.setDisabled(True)

        if self._num_inputs > 1:
            self._num_inputs -= 1
            self._update_inputs()

        self._add_button.setDisabled(False)
        self._remove_button.setDisabled(False)

    def _update_inputs(self):
        num_parents = self._num_inputs

        new_num_ports = {'input': num_parents, 'output': 1}
        new_data_types = {
            PortType.input: {},
            PortType.output: {0: VariableData.data_type}
        }
        new_port_captions = {
            'input': {},
            'output': {0: 'Out'}
        }

        for i in range(num_parents):
            new_data_types[PortType.input][i] = VariableData.data_type
            new_port_captions['input'][i] = "abcdefghijklmnopqrstuvwxyz"[i]  # 'In'

        self.ports_updated.emit(num_parents)

        # Build subclass with the appropriate number of inputs
        print("N{}_{}".format(num_parents, self._base_class.__name__))
        self.__class__ = type("N{}_{}".format(num_parents, self._base_class.__name__), (self._base_class,),
                              {'num_ports': new_num_ports,
                               'data_type': new_data_types,
                               'port_caption': new_port_captions,
                               'port_caption_visible': True,
                               'caption_visible': True,
                               'data_updated': self.data_updated,
                               'data_invalidated': self.data_invalidated,

                               'computing_started': self.computing_started,
                               'computing_finished': self.computing_finished,
                               'embedded_widget_size_updated': self.embedded_widget_size_updated,
                               'ports_updated': self.ports_updated,
                               'max_inputs': self.max_inputs
                               })

        # Trigger redraw
        s.CAUSAL_GRAPH_INITIALIZER.mark_stale()
        self.embedded_widget_size_updated.emit()
        self.data_updated.emit(0)


class EndogenousVariableDataModel(VariableInputNodeModel):
    name = "ABSTRACT Endogenous Variable"
    num_instances = 0

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)

        self._result = None
        self._validation_state = NodeValidationState.warning
        self._validation_message = 'Uninitialized'

        self._var_name = str(self.name) + f'_{type(self).num_instances}'
        self._var_id = self._var_name.lower()
        type(self).num_instances += 1
        self.node_label = QtWidgets.QLineEdit(self._var_name)
        self.main_widget.node_layout.addWidget(self.node_label)
        self.node_label.textChanged.connect(self.on_node_label_changed)

        self._parents = {}

    @property
    def caption(self):
        return self.name

    @property
    def num_parents(self):
        return self.num_ports['input']

    def on_node_label_changed(self):
        # TODO Ensure that node id is unique
        self._var_name = self.node_label.text()
        s.CAUSAL_GRAPH_INITIALIZER.mark_stale()
        self.data_updated.emit(0)

    def _check_inputs(self):

        # Remove stale parents
        for k in list(self._parents.keys()):
            if k not in self.data_type[PortType.input]:
                self._parents.pop(k)

        parents_ok = {}

        # Determine if each input is both connected and the correct type
        for p_idx, p_type in self.data_type[PortType.input].items():
            parents_ok[p_idx] = (p_idx in self._parents and
                                 self._parents[p_idx] is not None and
                                 self._parents[p_idx].data_type.id in ('variable',))

        #print(self._parents)
        #print(parents_ok)

        # If ANY of the inputs are unconnected or typed incorrectly, give the user a warning
        if not all(parents_ok.values()):
            self._validation_state = NodeValidationState.warning
            self._validation_message = "Missing or incorrect inputs"
            self._result = None
            self.data_updated.emit(0)
            return False

        # Otherwise, the node is valid
        self._validation_state = NodeValidationState.valid
        self._validation_message = ''
        self.data_updated.emit(0)
        return True

    @contextlib.contextmanager
    def _compute_lock(self):

        # Check if inputs are not set
        parents_ok = {}
        for p_idx, p_type in self.data_type[PortType.input].items():
            parents_ok[p_idx] = (p_idx in self._parents and
                                 self._parents[p_idx] is not None)

        if not all(parents_ok.values()):
            raise RuntimeError('Inputs not set.')

        # Set all the locks (make sure that we properly release the lock if we cannot use 'with' statements)
        with contextlib.ExitStack() as stack:
            locks = [stack.enter_context(self._parents[p_idx].lock)
                     for p_idx in self.data_type[PortType.input].keys()]
            yield

        # Mark that the data has been updated
        self.data_updated.emit(0)

    def out_data(self, port: int) -> NodeData:
        """
        The output data as a result of this calculation
        Parameters
        ----------
        port : int
        Returns
        -------
        value : NodeData
        """
        return self._result

    def set_in_data(self, data: NodeData, port: Port):
        """
        New data at the input of the node
        Parameters
        ----------
        data : NodeData
        port : Port
        """

        self._parents[port.index] = data

        if self._check_inputs():
            with self._compute_lock():
                self.compute()
        else:
            s.CAUSAL_GRAPH_INITIALIZER.mark_stale()

    def validation_state(self) -> NodeValidationState:
        return self._validation_state

    def validation_message(self) -> str:
        return self._validation_message

    def compute(self):
        ...


# Stub model for copying into new models with the correct boiler plate
class StubEndogenousVariableDataModel(EndogenousVariableDataModel):

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)

    def compute(self):
        pass


class TabularEndogenousVariableDataModel(EndogenousVariableDataModel):
    name = "Tabular"

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)

        self._table_layout = QtWidgets.QVBoxLayout()

        # Parameters widgets
        #self._num_layout
        self._choose_outputs = QtWidgets.QSpinBox()
        self._choose_outputs.setMinimum(1)
        self._choose_outputs.setMaximum(2)
        self._choose_outputs.setValue(2)

        # Table of probabilities
        self._labels = list(i for i in itertools.product(
            *[[c, '~'+c] for c in 'abcdefghijklmnopqrstuvwxyz'[:self.num_parents]]))
        self._table = np.ones((self._choose_outputs.value(), len(self._labels))) / self._choose_outputs.value()

        # Table Widget
        self._table_view = QtWidgets.QTableView()

        self._table_model = QStandardItemModel(0, 0)
        self._draw_table()
        self._table_view.setAlternatingRowColors(True)

        # In this iteration, we only want binary outputs to variables
        #self._table_layout.addWidget(self._choose_outputs)

        self._table_layout.addWidget(self._table_view)
        self.main_widget.node_layout.addLayout(self._table_layout)

        self._table_model.dataChanged.connect(self._table_updated)

    def compute(self):
        print("TABLUAR NODE COMPUTE")

        # Get list of parents
        parents = sorted([parent.variable_name for _, parent in self._parents.items()])

        # Create node
        s.CAUSAL_GRAPH_DEFINITION.add_node(self._var_name)

        print(self._table)
        table_cpd = TabularCPD(self._var_name, 2, self._table,
                                evidence=parents, evidence_card=[2] * len(parents))
        s.CAUSAL_GRAPH_DEFINITION.add_cpds(table_cpd)

        # Create edges
        for parent in parents:
            s.CAUSAL_GRAPH_DEFINITION.add_edge(parent, self._var_name)

        print(s.CAUSAL_GRAPH_DEFINITION)

        self._validation_state = NodeValidationState.valid
        self._validation_message = ''
        self._result = VariableData(self._var_id, self._var_name)




    def _update_inputs(self):
        super(TabularEndogenousVariableDataModel, self)._update_inputs()

        self._labels = list(i for i in itertools.product(
            *[[c, '~'+c] for c in 'abcdefghijklmnopqrstuvwxyz'[:self.num_parents]]))
        self._table = np.ones((self._choose_outputs.value(), len(self._labels))) / self._choose_outputs.value()

        self._draw_table()
        self.embedded_widget_size_updated.emit()
        self.data_updated.emit(0)

    def _draw_table(self):
        self._table_model.clear()

        for row in self._table:
            self._table_model.appendRow([QStandardItem(f"{n:.04f}") for n in row])

        self._table_model.setVerticalHeaderLabels([str(i) for i in range(self._table.shape[0])])
        self._table_model.setHorizontalHeaderLabels(['^'.join(i) for i in self._labels])

        # Trigger redraw
        self._table_view.setModel(self._table_model)
        self._table_view.resizeColumnsToContents()

    def _table_updated(self, qIndex):
        new_value = float(qIndex.data())

        if new_value > 1.0:
            new_value = 1.0

        if new_value < 0:
            new_value = 0

        self._table[qIndex.row(), qIndex.column()] = new_value
        self._table[int(not qIndex.row()), qIndex.column()] = 1 - new_value

        self._draw_table()

        s.CAUSAL_GRAPH_INITIALIZER.mark_stale()
        self.data_updated.emit(0)


"""
class EndogenousVariableDataModel(NodeDataModel):
    caption_visible = True
    num_ports = {
        'input': 1,
        'output': 1,
    }
    port_caption_visible = True
    data_type = ContinuousData.data_type

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._number1 = None
        self._number2 = None
        self._result = None
        self._validation_state = NodeValidationState.warning
        self._validation_message = 'Uninitialized'

    @property
    def caption(self):
        return self.name

    def _check_inputs(self):
        number1_ok = (self._number1 is not None and
                      self._number1.data_type.id in ('continuous', 'discrete'))
        number2_ok = (self._number2 is not None and
                      self._number2.data_type.id in ('continuous', 'discrete'))

        if not number1_ok or not number2_ok:
            self._validation_state = NodeValidationState.warning
            self._validation_message = "Missing or incorrect inputs"
            self._result = None
            self.data_updated.emit(0)
            return False

        self._validation_state = NodeValidationState.valid
        self._validation_message = ''
        return True

    @contextlib.contextmanager
    def _compute_lock(self):
        if not self._number1 or not self._number2:
            raise RuntimeError('inputs unset')

        with self._number1.lock:
            with self._number2.lock:
                yield

        self.data_updated.emit(0)

    def out_data(self, port: int) -> NodeData:
        '''
        The output data as a result of this calculation
        Parameters
        ----------
        port : int
        Returns
        -------
        value : NodeData
        '''
        return self._result

    def set_in_data(self, data: NodeData, port: Port):
        '''
        New data at the input of the node
        Parameters
        ----------
        data : NodeData
        port_index : int
        '''
        if port.index == 0:
            self._number1 = data
        elif port.index == 1:
            self._number2 = data

        if self._check_inputs():
            with self._compute_lock():
                self.compute()

    def validation_state(self) -> NodeValidationState:
        return self._validation_state

    def validation_message(self) -> str:
        return self._validation_message

    def compute(self):
        ...
"""

"""
class AdditionModel(MathOperationDataModel):
    name = "Addition"

    def compute(self):
        self._result = DecimalData(self._number1.number + self._number2.number)


class DivisionModel(MathOperationDataModel):
    name = "Division"
    port_caption = {'input': {0: 'Dividend',
                              1: 'Divisor',
                              },
                    'output': {0: 'Result'},
                    }

    def compute(self):
        if self._number2.number == 0.0:
            self._validation_state = NodeValidationState.error
            self._validation_message = "Division by zero error"
            self._result = None
        else:
            self._validation_state = NodeValidationState.valid
            self._validation_message = ''
            self._result = DecimalData(self._number1.number / self._number2.number)


class ModuloModel(MathOperationDataModel):
    name = 'Modulo'
    data_type = IntegerData.data_type
    port_caption = {'input': {0: 'Dividend',
                              1: 'Divisor',
                              },
                    'output': {0: 'Result'},
                    }

    def compute(self):
        if self._number2.number == 0.0:
            self._validation_state = NodeValidationState.error
            self._validation_message = "Division by zero error"
            self._result = None
        else:
            self._result = IntegerData(self._number1.number % self._number2.number)


class MultiplicationModel(MathOperationDataModel):
    name = 'Multiplication'
    port_caption = {'input': {0: 'A',
                              1: 'B',
                              },
                    'output': {0: 'Result'},
                    }

    def compute(self):
        self._result = DecimalData(self._number1.number * self._number2.number)


class NumberSourceDataModel(NodeDataModel):
    name = "NumberSource"
    caption_visible = False
    num_ports = {PortType.input: 0,
                 PortType.output: 1,
                 }
    port_caption = {'output': {0: 'Result'}}
    data_type = DecimalData.data_type

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._number = None
        self._line_edit = QLineEdit()
        self._line_edit.setValidator(QDoubleValidator())
        self._line_edit.setMaximumSize(self._line_edit.sizeHint())
        self._line_edit.textChanged.connect(self.on_text_edited)
        self._line_edit.setText("0.0")

    @property
    def number(self):
        return self._number

    def save(self) -> dict:
        'Add to the JSON dictionary to save the state of the NumberSource'
        doc = super().save()
        if self._number:
            doc['number'] = self._number.number
        return doc

    def restore(self, state: dict):
        'Restore the number from the JSON dictionary'
        try:
            value = float(state["number"])
        except Exception:
            ...
        else:
            self._number = DecimalData(value)
            self._line_edit.setText(self._number.number_as_text())

    def out_data(self, port: int) -> NodeData:
        '''
        The data output from this node
        Parameters
        ----------
        port : int
        Returns
        -------
        value : NodeData
        '''
        return self._number

    def embedded_widget(self) -> QWidget:
        'The number source has a line edit widget for the user to type in'
        return self._line_edit

    def on_text_edited(self, string: str):
        '''
        Line edit text has changed
        Parameters
        ----------
        string : str
        '''
        try:
            number = float(self._line_edit.text())
        except ValueError:
            self._data_invalidated.emit(0)
        else:
            self._number = DecimalData(number)
            self.data_updated.emit(0)


class NumberDisplayModel(NodeDataModel):
    name = "NumberDisplay"
    data_type = DecimalData.data_type
    caption_visible = False
    num_ports = {PortType.input: 1,
                 PortType.output: 0,
                 }
    port_caption = {'input': {0: 'Number'}}

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._number = None
        self._label = QLabel()
        self._label.setMargin(3)
        self._validation_state = NodeValidationState.warning
        self._validation_message = 'Uninitialized'

    def set_in_data(self, data: NodeData, port: Port):
        '''
        New data propagated to the input
        Parameters
        ----------
        data : NodeData
        int : int
        '''
        self._number = data
        number_ok = (self._number is not None and
                     self._number.data_type.id in ('decimal', 'integer'))

        if number_ok:
            self._validation_state = NodeValidationState.valid
            self._validation_message = ''
            self._label.setText(self._number.number_as_text())
        else:
            self._validation_state = NodeValidationState.warning
            self._validation_message = "Missing or incorrect inputs"
            self._label.clear()

        self._label.adjustSize()

    def embedded_widget(self) -> QWidget:
        'The number display has a label'
        return self._label


class SubtractionModel(MathOperationDataModel):
    name = "Subtraction"
    port_caption = {'input': {0: 'Minuend',
                              1: 'Subtrahend'
                              },
                    'output': {0: 'Result'},
                    }

    def compute(self):
        self._result = DecimalData(self._number1.number - self._number2.number)
"""

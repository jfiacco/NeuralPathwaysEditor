from qtpy.QtWidgets import QPushButton, QWidget, QTabWidget, QVBoxLayout

import NeuralPathways.session as s

from NeuralPathways.ui.attributes import AttributeWidget
from NeuralPathways.ui.activations import ActivationWidget
from NeuralPathways.ui.analysis import AnalysisWidget
from NeuralPathways.ui.causality import CausalityWidget
from NeuralPathways.utilities import SignalBridge

class AppTabs(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.bridgeLoadAttributes = SignalBridge()

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tab_attribue_view = QWidget()
        #self.tab_create_attributes = QWidget()
        self.tab_activation_viewer = QWidget()
        self.tab_pathways_viewer = QWidget()
        self.tab_causal_structure = QWidget()
        self.tabs.resize(300, 200)

        # Add tabs
        self.tabs.addTab(self.tab_attribue_view, "Attributes")
        #self.tabs.addTab(self.tab_create_attributes, "Create Attributes")
        self.tabs.addTab(self.tab_activation_viewer, "Extract")
        self.tabs.addTab(self.tab_pathways_viewer, "Pathways")
        self.tabs.addTab(self.tab_causal_structure, "Causal Structure")

        # Create attribute viewer tab
        self.tab_attribue_view.layout = QVBoxLayout(self)
        self.attributeWidget = AttributeWidget(self.bridgeLoadAttributes)
        self.tab_attribue_view.layout.addWidget(self.attributeWidget)
        #self.debugButton = QPushButton("DEBUG")
        #self.tab_attribue_view.layout.addWidget(self.debugButton)
        #self.debugButton.clicked.connect(self.debugPrint)
        self.tab_attribue_view.setLayout(self.tab_attribue_view.layout)

        # Create Activation Viewer tab
        self.tab_activation_viewer.layout = QVBoxLayout(self)
        self.activationWidget = ActivationWidget()
        self.tab_activation_viewer.layout.addWidget(self.activationWidget)
        #self.debugButton = QPushButton("DEBUG")
        #self.tab_activation_viewer.layout.addWidget(self.debugButton)
        #self.debugButton.clicked.connect(self.debugPrint)
        self.tab_activation_viewer.setLayout(self.tab_activation_viewer.layout)

        # Create Pathways Analysis tab
        self.tab_pathways_viewer.layout = QVBoxLayout(self)
        self.analysisWidget = AnalysisWidget(self.bridgeLoadAttributes)
        self.tab_pathways_viewer.layout.addWidget(self.analysisWidget)
        #self.debugButton = QPushButton("DEBUG")
        #self.tab_pathways_viewer.layout.addWidget(self.debugButton)
        #self.debugButton.clicked.connect(self.debugPrint)
        self.tab_pathways_viewer.setLayout(self.tab_pathways_viewer.layout)

        # Create Causality Tab
        # Create Pathways Analysis tab
        self.tab_causal_structure.layout = QVBoxLayout(self)
        self.causalityWidget = CausalityWidget(self.bridgeLoadAttributes)
        # TODO: complete causality tab
        # self.tab_causal_structure.layout.addWidget(self.causalityWidget)
        # self.debugButton = QPushButton("DEBUG")
        # self.tab_causal_structure.layout.addWidget(self.debugButton)
        # self.debugButton.clicked.connect(self.debugPrint)

        self.tab_causal_structure.setLayout(self.tab_causal_structure.layout)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def debugPrint(self):
        print(s.ATTRIBUTE_MODEL.df)
        s.ATTRIBUTE_MODEL.df["new"] = ['new' for n in range(len(s.ATTRIBUTE_MODEL.df))]
        s.ATTRIBUTE_MODEL.updateDataframe(s.ATTRIBUTE_MODEL.df)



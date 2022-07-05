from collections import OrderedDict

from NeuralPathways.models.pandas_model import PandasModel
from NeuralPathways.models.json_model import JsonModel
from NeuralPathways.utilities import SignalBridge

sig_attribute_loaded = SignalBridge()

ATTRIBUTE_MODEL = PandasModel()

ACTIVATION_MODEL = PandasModel()
ACTIVATION_DICT = {}
ACTIVATION_MATRIX = None
ACTIVATION_NEURONS = []

TOTAL_EXPLAINED_VARIANCE = 0.75
DIMENSIONALITY_REDUCTION = "PCA"

PATHWAYS_MODEL = None
PATHWAYS_ACTIVATIONS = None
PATHWAYS_INFO_MODEL = PandasModel()

ATTRIBUTE_CHECKLIST_STATE = OrderedDict()
DEFAULT_PROBE_THRESHOLD = 0.8
GOLD_LABEL_ATTRIBUTE = ""
PRED_LABEL_ATTRIBUTE = ""
ATTRIBUTE_ALIGNMENT_CLFS = {}
ATTRIBUTE_ALIGNMENT_SCORES = {}
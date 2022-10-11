import numpy as np

from functools import cached_property
from qtpy.QtCore import QObject, Signal
from qtpy.QtWidgets import QStyledItemDelegate
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT

from scipy.stats import pearsonr
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.utils.validation import check_X_y, check_array, check_is_fitted
from sklearn.utils.multiclass import unique_labels
from sklearn.metrics import euclidean_distances


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


class PearsonCorrelationClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, use_magnitude=False):
        self.use_magnitude = use_magnitude

        # This is used to be consistent with Logistic Regression
        self.coef_ = []
        self.correlation_matrix_ = None
        self.p_value_matrix_ = None
        self.classes_ = None


    def fit(self, X, y):
        # Check that X and y have correct shape
        X, y = check_X_y(X, y)

        # Store the classes seen during fit
        self.classes_ = unique_labels(y)

        # In the binary case we only need a vector
        if len(self.classes_) == 2 and self.classes_[0] == 0 and self.classes_[1] == 1:
            self.correlation_matrix_ = np.zeros((1, X.shape[1]))
            self.p_value_matrix_ = np.zeros((1, X.shape[1]))

            for i in range(X.shape[1]):
                self.correlation_matrix_[0, i], self.p_value_matrix_[0, i] = pearsonr(X[:, i], y)

        else:
            self.correlation_matrix_ = np.zeros((len(self.classes_), X.shape[1]))
            self.p_value_matrix_ = np.zeros((len(self.classes_), X.shape[1]))

            for i, cls in enumerate(self.classes_):
                for j in range(X.shape[1]):
                    target = np.array([1 if elem == cls else 0 for elem in y])
                    self.correlation_matrix_[i, j], self.p_value_matrix_[i, j] = pearsonr(X[:, j], target)

        self.coef_ = self.correlation_matrix_

        # Return the classifier
        return self

    def predict(self, X):
        # Check if fit has been called
        check_is_fitted(self)

        # Input validation
        X = check_array(X)

        #closest = np.argmin(euclidean_distances(X, self.X_), axis=1)
        return [self.classes_[0]] * X.shape[0]


class AlignmentDelegate(QStyledItemDelegate):
    @cached_property
    def alignment(self):
        return dict()

    def set_column_alignment(self, column, alignment):
        self.alignment[column] = alignment

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        alignment = self.alignment.get(index.column(), None)
        if alignment is not None:
            option.displayAlignment = alignment

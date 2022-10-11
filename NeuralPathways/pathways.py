import numpy as np

from enum import Enum
from sklearn.decomposition import PCA, FactorAnalysis, FastICA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import cohen_kappa_score
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning

import NeuralPathways.session as s
from NeuralPathways.utilities import PearsonCorrelationClassifier


class CorrelationMethod(Enum):
    PEARSON = 0
    LOG_REG = 1

def fa_pathways(X, explained_variance_required=0.999):
    exp_var = 0.0
    k = 0

    scaler = StandardScaler()
    X_in = scaler.fit_transform(X)

    while exp_var < explained_variance_required and k < X.shape[1]:
        k += 1
        fa_k = FactorAnalysis(n_components=k).fit(X_in)
        fa_loadings = fa_k.components_.T
        total_var = X_in.var(axis=0).sum()

        var_exp = np.sum(fa_loadings ** 2, axis=0)
        prop_var_exp = var_exp / total_var
        exp_var = np.sum(prop_var_exp)

        if prop_var_exp[-1] == 0:
            k -= 1
            break

    fa = FactorAnalysis(n_components=k)
    pathways = fa.fit_transform(X_in)

    fa_loadings = fa.components_.T
    total_var = X_in.var(axis=0).sum()

    var_exp = np.sum(fa_loadings ** 2, axis=0)
    prop_var_exp = var_exp / total_var

    return fa, pathways, fa.n_components, prop_var_exp

def extract_pathways(**args):

    if s.DIMENSIONALITY_REDUCTION == "PCA":
        s.PATHWAYS_MODEL = PCA(n_components=s.TOTAL_EXPLAINED_VARIANCE)
        s.PATHWAYS_ACTIVATIONS = s.PATHWAYS_MODEL.fit_transform(s.ACTIVATION_MATRIX)
        return s.PATHWAYS_MODEL.n_components_, s.PATHWAYS_MODEL.explained_variance_ratio_
    elif s.DIMENSIONALITY_REDUCTION == "Factor Analysis":
        s.PATHWAYS_MODEL, s.PATHWAYS_ACTIVATIONS, n_comp, exp_var = fa_pathways(s.ACTIVATION_MATRIX,
                                                                                s.TOTAL_EXPLAINED_VARIANCE)
        return n_comp, exp_var
    else:
        print("ERROR: unknown dimensionality reduction technique selected")

def compute_pathway_alignments(**args):
    s.ATTRIBUTE_ALIGNMENT_CLFS = {}
    s.ATTRIBUTE_ALIGNMENT_SCORES = {}

    if s.PATHWAYS_ACTIVATIONS is None:
        print("ERROR: pathways must be extracted.")

    if args['method'] != CorrelationMethod.LOG_REG and args['method'] != CorrelationMethod.PEARSON:
        print("ERROR: unknown correlation method attempted")

    for attribute, state in s.ATTRIBUTE_CHECKLIST_STATE.items():
        if not state['checked']:
            continue

        if args['method'] == CorrelationMethod.LOG_REG:
            clf = LogisticRegression()
        else:
            clf = PearsonCorrelationClassifier()

        try:
            clf.fit(s.PATHWAYS_ACTIVATIONS, s.ATTRIBUTE_MODEL.df[attribute])

            s.ATTRIBUTE_ALIGNMENT_CLFS[attribute] = clf
            s.ATTRIBUTE_ALIGNMENT_SCORES[attribute] = clf.score(s.PATHWAYS_ACTIVATIONS, s.ATTRIBUTE_MODEL.df[attribute])

            preds = clf.predict(s.PATHWAYS_ACTIVATIONS)

        except ConvergenceWarning as e:
            pass
        print(attribute, cohen_kappa_score(preds, s.ATTRIBUTE_MODEL.df[attribute]))
import numpy as np

from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import cohen_kappa_score
from sklearn.exceptions import ConvergenceWarning

import NeuralPathways.session as s


def extract_pathways(**args):

    if s.DIMENSIONALITY_REDUCTION == "PCA":
        s.PATHWAYS_MODEL = PCA(n_components=s.TOTAL_EXPLAINED_VARIANCE)
        s.PATHWAYS_ACTIVATIONS = s.PATHWAYS_MODEL.fit_transform(s.ACTIVATION_MATRIX)
        return s.PATHWAYS_MODEL.n_components_, s.PATHWAYS_MODEL.explained_variance_ratio_

    else:
        print("ERROR: unknown dimensionality reduction technique selected")

def compute_pathway_alignments(**args):
    s.ATTRIBUTE_ALIGNMENT_CLFS = {}
    s.ATTRIBUTE_ALIGNMENT_SCORES = {}

    if s.PATHWAYS_ACTIVATIONS is None:
        print("ERROR: pathways must be extracted.")

    for attribute, state in s.ATTRIBUTE_CHECKLIST_STATE.items():
        if not state['checked']:
            continue

        clf = LogisticRegression()
        try:
            clf.fit(s.PATHWAYS_ACTIVATIONS, s.ATTRIBUTE_MODEL.df[attribute])

            s.ATTRIBUTE_ALIGNMENT_CLFS[attribute] = clf
            s.ATTRIBUTE_ALIGNMENT_SCORES[attribute] = clf.score(s.PATHWAYS_ACTIVATIONS, s.ATTRIBUTE_MODEL.df[attribute])

            preds = clf.predict(s.PATHWAYS_ACTIVATIONS)

        except ConvergenceWarning as e:
            pass
        print(attribute, cohen_kappa_score(preds, s.ATTRIBUTE_MODEL.df[attribute]))
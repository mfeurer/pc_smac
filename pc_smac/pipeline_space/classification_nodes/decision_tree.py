


# The algorithm and hyperparameter spaces come from https://github.com/automl/auto-sklearn

import numpy as np

from ConfigSpace.configuration_space import ConfigurationSpace
from ConfigSpace.hyperparameters import UniformFloatHyperparameter, \
    UniformIntegerHyperparameter, CategoricalHyperparameter, \
    UnParametrizedHyperparameter, Constant

from pc_smac.pc_smac.pipeline_space.node import Node, ClassificationAlgorithm
from pc_smac.pc_smac.utils.constants import *
from pc_smac.pc_smac.utils.util_implementations import convert_multioutput_multiclass_to_multilabel


class DecisionTreeNode(Node):

    def __init__(self):
        self.name = "decision_tree"
        self.type = "classifier"
        self.hyperparameters = {"criterion": "gini", "splitter": "best", "max_features": 1.0,
                                "max_depth": 0.5, "min_samples_split": 2, "min_samples_leaf": 1,
                                "min_weight_fraction_leaf": 0.0, "max_leaf_nodes": "None"}
        self.algorithm = DecisionTree

    def initialize_algorithm(self, hyperparameters):
        hyperparameters = self.initialize_hyperparameters(hyperparameters)
        decision_tree = self.algorithm(criterion=hyperparameters["criterion"], # actual hp
                                       splitter=hyperparameters["splitter"],
                                       max_features=hyperparameters["max_features"],
                                       max_depth=hyperparameters["max_depth"], # actual hp
                                       min_samples_split=hyperparameters["min_samples_split"], # actual hp
                                       min_samples_leaf=hyperparameters["min_samples_leaf"], # actual hp
                                       min_weight_fraction_leaf=hyperparameters["min_weight_fraction_leaf"],
                                       max_leaf_nodes=hyperparameters["max_leaf_nodes"])

        return (self.get_full_name(), decision_tree)

    def get_hyperparameter_search_space(self, dataset_properties=None):
        return self.algorithm.get_hyperparameter_search_space(dataset_properties=dataset_properties)

    def get_properties(self, dataset_properties=None):
        return self.algorithm.get_properties(dataset_properties=dataset_properties)


class DecisionTree(ClassificationAlgorithm):
    def __init__(self, criterion, splitter, max_features, max_depth,
                 min_samples_split, min_samples_leaf, min_weight_fraction_leaf,
                 max_leaf_nodes, class_weight=None, random_state=None):
        self.criterion = criterion
        self.splitter = splitter
        self.max_features = max_features
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_leaf_nodes = max_leaf_nodes
        self.min_weight_fraction_leaf = min_weight_fraction_leaf
        self.random_state = random_state
        self.class_weight = class_weight
        self.estimator = None

    def fit(self, X, y, sample_weight=None):
        from sklearn.tree import DecisionTreeClassifier

        self.max_features = float(self.max_features)
        if self.max_depth == "None":
            max_depth = self.max_depth = None
        else:
            num_features = X.shape[1]
            self.max_depth = int(self.max_depth)
            max_depth = max(1, int(np.round(self.max_depth * num_features, 0)))
        self.min_samples_split = int(self.min_samples_split)
        self.min_samples_leaf = int(self.min_samples_leaf)
        if self.max_leaf_nodes == "None" or self.max_leaf_nodes == None:
            self.max_leaf_nodes = None
        else:
            self.max_leaf_nodes = int(self.max_leaf_nodes)
        self.min_weight_fraction_leaf = float(self.min_weight_fraction_leaf)

        self.estimator = DecisionTreeClassifier(
            criterion=self.criterion,
            max_depth=max_depth,
            min_samples_split=self.min_samples_split,
            min_samples_leaf=self.min_samples_leaf,
            max_leaf_nodes=self.max_leaf_nodes,
            class_weight=self.class_weight,
            random_state=self.random_state)
        self.estimator.fit(X, y, sample_weight=sample_weight)
        return self

    def predict(self, X):
        if self.estimator is None:
            raise NotImplementedError
        return self.estimator.predict(X)

    def predict_proba(self, X):
        if self.estimator is None:
            raise NotImplementedError()
        probas = self.estimator.predict_proba(X)
        probas = convert_multioutput_multiclass_to_multilabel(probas)
        return probas

    @staticmethod
    def get_properties(dataset_properties=None):
        return {'shortname': 'DT',
                'name': 'Decision Tree Classifier',
                'handles_regression': False,
                'handles_classification': True,
                'handles_multiclass': True,
                'handles_multilabel': True,
                'is_deterministic': True,
                'input': (DENSE, SPARSE, UNSIGNED_DATA),
                'output': (PREDICTIONS,)}

    @staticmethod
    def get_hyperparameter_search_space(dataset_properties=None):
        cs = ConfigurationSpace()

        criterion = cs.add_hyperparameter(CategoricalHyperparameter(
            "criterion", ["gini", "entropy"], default="gini"))
        #splitter = cs.add_hyperparameter(Constant("splitter", "best"))
        #max_features = cs.add_hyperparameter(Constant('max_features', 1.0))
        max_depth = cs.add_hyperparameter(UniformFloatHyperparameter(
            'max_depth', 0., 2., default=0.5))
        min_samples_split = cs.add_hyperparameter(UniformIntegerHyperparameter(
            "min_samples_split", 2, 20, default=2))
        min_samples_leaf = cs.add_hyperparameter(UniformIntegerHyperparameter(
            "min_samples_leaf", 1, 20, default=1))
        #min_weight_fraction_leaf = cs.add_hyperparameter(
        #    Constant("min_weight_fraction_leaf", 0.0))
        #max_leaf_nodes = cs.add_hyperparameter(
        #    UnParametrizedHyperparameter("max_leaf_nodes", "None"))

        return cs

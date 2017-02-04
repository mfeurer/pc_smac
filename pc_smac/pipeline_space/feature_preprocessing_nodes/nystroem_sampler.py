import numpy as np

from ConfigSpace.configuration_space import ConfigurationSpace
from ConfigSpace.hyperparameters import UniformFloatHyperparameter, \
    UniformIntegerHyperparameter, CategoricalHyperparameter
from ConfigSpace.conditions import InCondition, EqualsCondition, AndConjunction

from pc_smac.pc_smac.pipeline_space.node import Node, PreprocessingAlgorithm
from pc_smac.pc_smac.utils.constants import *



class NystroemSamplerNode(Node):
    def __init__(self):
        self.name = "nystroem_sampler"
        self.type = "feature_preprocessor"
        self.hyperparameters = {"n_components": 100, "kernel": "rbf", "degree": 3,
                                "gamma": 1.0, "coef0": 0.0}
        self.algorithm = Nystroem

    def initialize_algorithm(self, hyperparameters):

        hyperparameters = self.initialize_hyperparameters(hyperparameters)
        nystroem_sampler = self.algorithm(kernel=hyperparameters["kernel"],
                                     n_components=hyperparameters["n_components"],
                                     gamma=hyperparameters["gamma"],
                                     degree=hyperparameters["degree"],
                                     coef0=hyperparameters["coef0"],
                                     random_state=None)

        return (self.get_full_name(), nystroem_sampler)

    def get_hyperparameter_search_space(self, dataset_properties=None):
        return self.algorithm.get_hyperparameter_search_space(dataset_properties=dataset_properties)

    def get_properties(self, dataset_properties=None):
        return self.algorithm.get_properties(dataset_properties=dataset_properties)


class Nystroem(PreprocessingAlgorithm):
    def __init__(self, kernel, n_components, gamma=1.0, degree=3,
                 coef0=1, random_state=None):
        self.kernel = kernel
        self.n_components = int(n_components)
        self.gamma = float(gamma)
        self.degree = int(degree)
        self.coef0 = float(coef0)
        self.random_state = random_state

    def fit(self, X, Y=None):
        import scipy.sparse
        import sklearn.kernel_approximation

        self.preprocessor = sklearn.kernel_approximation.Nystroem(
            kernel=self.kernel, n_components=self.n_components,
            gamma=self.gamma, degree=self.degree, coef0=self.coef0,
            random_state=self.random_state)

        # Because the pipeline guarantees that each feature is positive,
        # clip all values below zero to zero
        if self.kernel == 'chi2':
            if scipy.sparse.issparse(X):
                X.data[X.data < 0] = 0.0
            else:
                X[X < 0] = 0.0

        self.preprocessor.fit(X.astype(np.float64))
        return self

    def transform(self, X):
        import scipy.sparse

        # Because the pipeline guarantees that each feature is positive,
        # clip all values below zero to zero
        if self.kernel == 'chi2':
            if scipy.sparse.issparse(X):
                X.data[X.data < 0] = 0.0
            else:
                X[X < 0] = 0.0

        if self.preprocessor is None:
            raise NotImplementedError()
        return self.preprocessor.transform(X)

    @staticmethod
    def get_properties(dataset_properties=None):
        data_type = UNSIGNED_DATA

        if dataset_properties is not None:
            signed = dataset_properties.get('signed')
            if signed is not None:
                data_type = SIGNED_DATA if signed is True else UNSIGNED_DATA
        return {'shortname': 'Nystroem',
                'name': 'Nystroem kernel approximation',
                'handles_regression': True,
                'handles_classification': True,
                'handles_multiclass': True,
                'handles_multilabel': True,
                'is_deterministic': True,
                'input': (SPARSE, DENSE, data_type),
                'output': (INPUT, UNSIGNED_DATA)}

    @staticmethod
    def get_hyperparameter_search_space(dataset_properties=None):
        if dataset_properties is not None and \
                (dataset_properties.get("sparse") is True or
                 dataset_properties.get("signed") is False):
            allow_chi2 = False
        else:
            allow_chi2 = True

        possible_kernels = ['poly', 'rbf', 'sigmoid', 'cosine']
        if allow_chi2:
            possible_kernels.append("chi2")
        kernel = CategoricalHyperparameter('kernel', possible_kernels, 'rbf')
        degree = UniformIntegerHyperparameter('degree', 2, 5, 3)
        gamma = UniformFloatHyperparameter("gamma", 3.0517578125e-05, 8,
                                           log=True, default=0.1)
        coef0 = UniformFloatHyperparameter("coef0", -1, 1, default=0)
        n_components = UniformIntegerHyperparameter(
            "n_components", 50, 10000, default=100, log=True)

        cs = ConfigurationSpace()
        cs.add_hyperparameter(kernel)
        cs.add_hyperparameter(degree)
        cs.add_hyperparameter(gamma)
        cs.add_hyperparameter(coef0)
        cs.add_hyperparameter(n_components)

        degree_depends_on_poly = EqualsCondition(degree, kernel, "poly")
        coef0_condition = InCondition(coef0, kernel, ["poly", "sigmoid"])

        gamma_kernels = ["poly", "rbf", "sigmoid"]
        if allow_chi2:
            gamma_kernels.append("chi2")
        gamma_condition = InCondition(gamma, kernel, gamma_kernels)
        cs.add_condition(degree_depends_on_poly)
        cs.add_condition(coef0_condition)
        cs.add_condition(gamma_condition)
        return cs


from ConfigSpace.configuration_space import ConfigurationSpace
from ConfigSpace.hyperparameters import CategoricalHyperparameter


from pc_smac.pc_smac.pipeline_space.node import Node, PreprocessingAlgorithm
from pc_smac.pc_smac.utils.constants import *

class ImputationNode(Node):

    def __init__(self):
        self.name = "imputation"
        self.type = "imputation"
        self.hyperparameters = {"strategy": "mean"}
        self.algorithm = Imputation

    def initialize_algorithm(self, hyperparameters):
        hyperparameters = self.initialize_hyperparameters(hyperparameters)
        imputation = self.algorithm(strategy=self.hyperparameters["strategy"])
        return (self.get_full_name(), imputation)

    def get_hyperparameter_search_space(self, dataset_properties=None):
        return self.algorithm.get_hyperparameter_search_space(dataset_properties=dataset_properties)

    def get_properties(self, dataset_properties=None):
        return self.algorithm.get_properties(dataset_properties=dataset_properties)


class Imputation(PreprocessingAlgorithm):
    def __init__(self, strategy='median', random_state=None):
        # TODO pay attention to the cases when a copy is made (CSR matrices)
        self.strategy = strategy

    def get_params(self, deep):
        return {
            'strategy': self.strategy
        }

    def fit(self, X, y=None):
        import sklearn.preprocessing

        self.preprocessor = sklearn.preprocessing.Imputer(
            strategy=self.strategy, copy=False)
        self.preprocessor = self.preprocessor.fit(X)
        return self

    def transform(self, X):
        if self.preprocessor is None:
            raise NotImplementedError()
        return self.preprocessor.transform(X)

    @staticmethod
    def get_properties(dataset_properties=None):
        return {'shortname': 'Imputation',
                'name': 'Imputation',
                'handles_missing_values': True,
                'handles_nominal_values': True,
                'handles_numerical_features': True,
                'prefers_data_scaled': False,
                'prefers_data_normalized': False,
                'handles_regression': True,
                'handles_classification': True,
                'handles_multiclass': True,
                'handles_multilabel': True,
                'is_deterministic': True,
                # TODO find out of this is right!
                'handles_sparse': True,
                'handles_dense': True,
                'input': (DENSE, SPARSE, UNSIGNED_DATA),
                'output': (INPUT,),
                'preferred_dtype': None}

    @staticmethod
    def get_hyperparameter_search_space(dataset_properties=None):
        # TODO add replace by zero!
        strategy = CategoricalHyperparameter(
            "strategy", ["mean", "median", "most_frequent"], default="mean")
        cs = ConfigurationSpace()
        cs.add_hyperparameter(strategy)
        return cs

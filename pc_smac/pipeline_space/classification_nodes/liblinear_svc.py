
# The algorithm and hyperparameter spaces come from https://github.com/automl/auto-sklearn

from ConfigSpace.configuration_space import ConfigurationSpace
from ConfigSpace.hyperparameters import UniformFloatHyperparameter, \
    CategoricalHyperparameter, Constant
from ConfigSpace.forbidden import ForbiddenEqualsClause, \
    ForbiddenAndConjunction

from pc_smac.pc_smac.pipeline_space.node import Node, ClassificationAlgorithm
from pc_smac.pc_smac.utils.constants import *
from pc_smac.pc_smac.utils.util_implementations import softmax




class LibLinear_SVC_Node(Node):

    def __init__(self):
        self.name = "liblinear_svc"
        self.type = "classifier"
        self.hyperparameters = {"penalty": "l2", "loss": "squared_hinge", "dual": "False", "tol": 1e-4,
                                "C": 1.0, "multi_class": "ovr", "fit_intercept": "True", "intercept_scaling": 1}
        self.algorithm = LibLinear_SVC

    def initialize_algorithm(self, hyperparameters):
        hyperparameters = self.initialize_hyperparameters(hyperparameters)
        liblinear_svc = self.algorithm(penalty=hyperparameters["penalty"],  # actual hp
                                       loss=hyperparameters["loss"],  # actual hp
                                       dual=hyperparameters["dual"],
                                       tol=hyperparameters["tol"],  # actual hp
                                       C=hyperparameters["C"],  # actual hp
                                       multi_class=hyperparameters["multi_class"],
                                       fit_intercept=hyperparameters["fit_intercept"],
                                       intercept_scaling=hyperparameters["intercept_scaling"]
                                       )

        return (self.get_full_name(), liblinear_svc)

    def get_hyperparameter_search_space(self, dataset_properties=None):
        return self.algorithm.get_hyperparameter_search_space(dataset_properties=dataset_properties)

    def get_properties(self, dataset_properties=None):
        return self.algorithm.get_properties(dataset_properties=dataset_properties)

class LibLinear_SVC(ClassificationAlgorithm):
    # Liblinear is not deterministic as it uses a RNG inside
    def __init__(self, penalty, loss, dual, tol, C, multi_class,
                 fit_intercept, intercept_scaling, class_weight=None,
                 random_state=None):
        self.penalty = penalty
        self.loss = loss
        self.dual = dual
        self.tol = tol
        self.C = C
        self.multi_class = multi_class
        self.fit_intercept = fit_intercept
        self.intercept_scaling = intercept_scaling
        self.class_weight = class_weight
        self.random_state = random_state
        self.estimator = None

    def fit(self, X, Y):
        import sklearn.svm
        import sklearn.multiclass

        self.C = float(self.C)
        self.tol = float(self.tol)

        self.dual = self.dual == 'True'
        self.fit_intercept = self.fit_intercept == 'True'
        self.intercept_scaling = float(self.intercept_scaling)

        if self.class_weight == "None":
            self.class_weight = None

        estimator = sklearn.svm.LinearSVC(penalty=self.penalty,
                                          loss=self.loss,
                                          dual=self.dual,
                                          tol=self.tol,
                                          C=self.C,
                                          class_weight=self.class_weight,
                                          fit_intercept=self.fit_intercept,
                                          intercept_scaling=self.intercept_scaling,
                                          multi_class=self.multi_class,
                                          random_state=self.random_state)

        if len(Y.shape) == 2 and Y.shape[1] > 1:
            self.estimator = sklearn.multiclass.OneVsRestClassifier(estimator, n_jobs=1)
        else:
            self.estimator = estimator

        self.estimator.fit(X, Y)
        return self

    def predict(self, X):
        if self.estimator is None:
            raise NotImplementedError()
        return self.estimator.predict(X)

    def predict_proba(self, X):
        if self.estimator is None:
            raise NotImplementedError()

        df = self.estimator.decision_function(X)
        return softmax(df)

    @staticmethod
    def get_properties(dataset_properties=None):
        return {'shortname': 'Liblinear-SVC',
                'name': 'Liblinear Support Vector Classification',
                'handles_regression': False,
                'handles_classification': True,
                'handles_multiclass': True,
                'handles_multilabel': True,
                'is_deterministic': False,
                'input': (SPARSE, DENSE, UNSIGNED_DATA),
                'output': (PREDICTIONS,)}

    @staticmethod
    def get_hyperparameter_search_space(dataset_properties=None):
        cs = ConfigurationSpace()

        penalty = cs.add_hyperparameter(CategoricalHyperparameter(
            "penalty", ["l1", "l2"], default="l2"))
        loss = cs.add_hyperparameter(CategoricalHyperparameter(
            "loss", ["hinge", "squared_hinge"], default="squared_hinge"))
        # dual = cs.add_hyperparameter(Constant("dual", "False"))
        # This is set ad-hoc
        tol = cs.add_hyperparameter(UniformFloatHyperparameter(
            "tol", 1e-5, 1e-1, default=1e-4, log=True))
        C = cs.add_hyperparameter(UniformFloatHyperparameter(
            "C", 0.03125, 32768, log=True, default=1.0))
        # multi_class = cs.add_hyperparameter(Constant("multi_class", "ovr"))
        # These are set ad-hoc
        # fit_intercept = cs.add_hyperparameter(Constant("fit_intercept", "True"))
        # intercept_scaling = cs.add_hyperparameter(Constant(
        #    "intercept_scaling", 1))

        penalty_and_loss = ForbiddenAndConjunction(
            ForbiddenEqualsClause(penalty, "l1"),
            ForbiddenEqualsClause(loss, "hinge")
        )
        constant_penalty_and_loss = ForbiddenAndConjunction(
            # ForbiddenEqualsClause(dual, "False"),
            ForbiddenEqualsClause(penalty, "l2"),
            ForbiddenEqualsClause(loss, "hinge")
        )
        penalty_and_dual = ForbiddenEqualsClause(penalty, "l1")

        # penalty_and_dual = ForbiddenAndConjunction(
        #     ForbiddenEqualsClause(dual, "False"),
        #     ForbiddenEqualsClause(penalty, "l1")
        # )
        cs.add_forbidden_clause(penalty_and_loss)
        cs.add_forbidden_clause(constant_penalty_and_loss)
        cs.add_forbidden_clause(penalty_and_dual)
        return cs

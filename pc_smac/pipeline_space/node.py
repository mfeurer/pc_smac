
import abc

class Node(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    def get_name(self):
        return self.name

    def get_full_name(self):
        return self.type + ":" + self.name

    def get_hyperparameters(self):
        return self.hyperparameters.keys()

    def initialize_hyperparameters(self, hyperparameters):
        for hp in self.get_hyperparameters():
            if hp not in hyperparameters or hyperparameters[hp] == None:
                hyperparameters[hp] = self.hyperparameters[hp]
        return hyperparameters

    @abc.abstractmethod
    def initialize_algorithm(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_hyperparameter_space(self):
        raise NotImplementedError


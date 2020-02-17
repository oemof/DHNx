from addict import Dict


class Model():
    r"""
    Abstract base class for different kind of models.
    """
    def __init__(self, thermal_network):
        self.network = thermal_network
        self.setup()
        self.results = Dict()

    def setup(self):
        pass

    def solve(self):
        pass

    def get_results(self):
        pass

    def is_consistent(self):
        pass


class OperationOptimizationModel(Model):
    r"""
    Abstract base class for operational optimization models.
    """
    def __init__(self, thermal_network):
        super().__init__(thermal_network)
        self.is_consistent()
        self.results = ['a', 'b']

    def is_consistent(self):
        # TODO.
        pass


class InvestOptimizationModel(Model):
    r"""
    Abstract base class for investment optimization models.
    """
    def __init__(self, thermal_network):
        super().__init__(thermal_network)
        self.is_consistent()
        self.results = ['a', 'b']

    def is_consistent(self):
        # TODO.
        pass


class SimulationModel(Model):
    r"""
    Abstract base class for simulation models.
    """
    def __init__(self, thermal_network):
        super().__init__(thermal_network)
        self.is_consistent()
        self.results = ['a', 'b']

    def is_consistent(self):
        # TODO.
        pass

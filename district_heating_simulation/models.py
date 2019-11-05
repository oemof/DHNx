import oemof


class OperationOptimizationModel():
    def __init__(self, thermal_network, problem):
        self.network = thermal_network
        self.problem = problem
        self.results = None

    def solve(self):
        results = None
        return results


class InvestOptimizationModel():
    def __init__(self, thermal_network, problem):
        pass

    def solve(self):
        return None


class SimulationModel():
    def __init__(self, thermal_network, problem):
        pass

    def solve(self):
        return None

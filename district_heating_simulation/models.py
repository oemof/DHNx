import os
import pandas as pd


class OperationOptimizationModel():
    def __init__(self, thermal_network, problem):
        self.network = thermal_network
        self.problem = problem
        self.results = None

    def solve(self):
        global_res = pd.DataFrame([1])
        heat_flow_edges = pd.DataFrame([1])
        heat_flow_producer = pd.DataFrame([1])

        results = {
            'global': global_res,
            'heat_flow_edge': heat_flow_edges,
            'heat_flow_producer': heat_flow_producer
        }

        self.results = results

        return results

    def results_to_csv(self, dir):
        if not os.path.exists(dir):
            os.mkdir(dir)

        for name, item in self.results.items():
            item.to_csv(os.path.join(dir, name + '.csv'))


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

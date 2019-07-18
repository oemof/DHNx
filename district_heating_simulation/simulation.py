import networkx as nx
import numpy as np
import pandas as pd


class SimulationModel():
    r"""
    Simulation model for ThermalNetwork
    """

    def __init__(self, thermal_network):
        self.thermal_network = thermal_network
        self.problem = {}
        self.results = {}

    def _has_loops(self):
        return False # TODO: self.thermal_network.has_loops()

    def _solve_hydraulic(self):
        graph = self.thermal_network.get_nx_graph()
        inc_matrix = nx.incidence_matrix(graph,
                                         oriented=True).todense()
        n_nodes = len(graph.nodes)
        mass_flow_edges = np.zeros((len(self.problem['snapshots']), len(graph.edges)))
        for t in self.problem['snapshots']:
            mass_flow_nodes = self.problem['mass_flow_cons'].loc[t].\
            reindex([str(i) for i in range(n_nodes)], fill_value=0)
            mass_flow_nodes[0] = - np.sum(mass_flow_nodes[1:])
            mass_flow_edges[t,:] = np.linalg.lstsq(inc_matrix, mass_flow_nodes, rcond=None)[0]

        columns = self.thermal_network.edges.index
        mass_flow_edges = pd.DataFrame(mass_flow_edges, columns=columns)
        mass_flow_edges.index.name = 'snapshots'
        self.results['mass_flow_edges'] = mass_flow_edges

    def _solve_thermal(self):
        temperature = pd.DataFrame({'node_id': [0], 'temperature_inlet': [0], 'temperature_return': [1]})
        self.results['temperature'] = temperature

    def _calculate_pump_power(self):
        return 0

    def _calculate_heat_feed_in(self):
        return 0

    def _calculate_heat_consumed(self):
        return 0

    def _calculate_heat_losses(self):
        return 0

    def _collect_summary_results(self):
        self.results['general'] = pd.DataFrame({'snapshot': [0],
                                                'pump_power': [0],
                                                'heat_feed_in': [0],
                                                'heat_consumed': [0],
                                                'heat_losses': [0]}).set_index('snapshot')

    def set_problem(self, mass_flow_cons, temperature_drop_cons):
        # TODO: if mass_flow_cons.index != temperature_drop_cons.index:
        # TODO:     raise('Error: Problem has conflicting indices.')
        self.problem['snapshots'] = mass_flow_cons.index
        self.problem['mass_flow_cons'] = mass_flow_cons
        self.problem['temperature_drop_cons'] = temperature_drop_cons

    def solve(self):
        if self._has_loops():
            pass

        else:
            self._solve_hydraulic()
            self._solve_thermal()
            self._collect_summary_results()

        return self.results


class SimulationModelTespy(SimulationModel):
    r"""
    Simulation model for ThermalNetwork using tespy
    """

    def __init__(self, thermal_network):
        self.thermal_network = thermal_network

    def set_problem(self):
        pass

    def create_tespy_model(self):
        return tespy_model

    def solve(self):
        results = 0
        thermal_network.results = results
        return thermal_network


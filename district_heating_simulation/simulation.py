import networkx as nx
import numpy as np
import pandas as pd


class SimulationModel():
    r"""
    Simulation model for ThermalNetwork
    """

    def __init__(self, thermal_network):
        self.thermal_network = thermal_network

    def set_problem(self):

    def solve(self):
        results = {}
        results['mass_flows'] = pd.DataFrame()
        results['temperatures'] = pd.DataFrame()
        results['general'] = pd.DataFrame({'snapshot': [0],
                                           'pump_power': [0],
                                           'heat_feed_in': [0],
                                           'heat_consumed': [0],
                                           'heat_losses': [0]}).set_index('snapshot')
        self.thermal_network.results = results
        return self.thermal_network


class SimulationModelTespy(SimulationModel):
    r"""
    Simulation model for ThermalNetwork using tespy
    """

    def __init__(self, thermal_network):
        self.thermal_network = thermal_network

    def set_problem(self):

    def create_tespy_model(self):
        return tespy_model

    def solve(self):
        results = 0
        thermal_network.results = results
        return thermal_network


def hydraulics_known_flows_wo_loops(G, m_node):
    A = nx.incidence_matrix(G, oriented=True).todense()
    m_node[0] = - np.sum(m_node[1:])
    print(m_node.shape)
    print(A.shape)
    flows = np.linalg.lstsq(A,m_node)[0]
    return flows

def hydraulics_known_flows_wo_loops_v2(G, m_node):
    A = nx.incidence_matrix(G, oriented=True).todense()
    A = A[1:,:]
    m_node = m_node[1:]
    flows = np.linalg.solve(A, m_node)
    return flows

def hydraulics_known_flows_wo_loops_sparse(G, m_node):
    import scipy
    A = nx.incidence_matrix(G, oriented=True)
    A = A[1:,:]
    m_node = m_node[1:]
    flows = scipy.sparse.linalg.spsolve(A, m_node)
    return flows


def hydraulics_known_flows_wo_loops_prop_to_edges(G, m_node):
    A = nx.incidence_matrix(G, oriented=True).todense()
    A = A[1:,:]
    m_node = m_node[1:]
    flows = np.linalg.solve(A, m_node)
    G = properties_to_edges(G, {'mass_flows': flows})
    return flows

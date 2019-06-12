import networkx as nx
import numpy as np

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

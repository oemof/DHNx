import pandas as pd
import networkx as nx


def thermal_network_to_nx_graph(thermal_network):
    r"""

    Parameters
    ----------
    thermal_network

    Returns
    -------
    nx_graph : nx:MultiDigraph
        networkx graph of thermal_network
    """
    nx_graph = nx.MultiDiGraph()  # TODO: Check if this line can be removed.

    edge_attr = list(thermal_network.components['edges'].columns)

    edge_attr.remove('from_node')

    edge_attr.remove('to_node')

    nx_graph = nx.from_pandas_edgelist(
        thermal_network.components['edges'],
        'from_node',
        'to_node',
        edge_attr=edge_attr,
        create_using=thermal_network.graph
    )

    nodes = pd.concat([thermal_network.components['producers'],  # TODO: Introduce a 'node' type
                       thermal_network.components['consumers'],
                       thermal_network.components['forks']], axis=0)

    node_attrs = {node_id: dict(data) for node_id, data in nodes.iterrows()}

    nx.set_node_attributes(nx_graph, node_attrs)

    return nx_graph


def nx_graph_to_thermal_network(nx_graph):
    r"""
    Creates ThermalNetwork from nx.MultiDigraph

    Parameters
    ----------
    nx_graph : nx.MultiDigraph

    Returns
    -------
    thermal_network : ThermalNetwork
    """
    raise NotImplementedError('This feature is not implemented yet.')

# -*- coding: utf-8

"""
This module is designed to hold functions to convert ThermalNetworks into
networkx a graph.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

import networkx as nx
import pandas as pd


def thermal_network_to_nx_graph(thermal_network):
    r"""

    Parameters
    ----------
    thermal_network : dhnx.network.ThermalNetwork

    Returns
    -------
    nx_graph : nx:MultiDigraph
        networkx graph of thermal_network
    """
    nx_graph = nx.DiGraph()  # TODO: Check if this line can be removed.

    edges = thermal_network.components['pipes'].copy()

    edge_attr = list(edges.columns)

    edge_attr.remove('from_node')

    edge_attr.remove('to_node')

    nx_graph = nx.from_pandas_edgelist(
        edges,
        'from_node',
        'to_node',
        edge_attr=edge_attr,
        create_using=nx_graph
    )

    nodes = {
        list_name: thermal_network.components[list_name].copy() for list_name in [
            'consumers',  # TODO: Do not hard code these here
            'producers',
            'forks'
        ]
    }

    for k, v in nodes.items():
        v.index = [k + '-' + str(id) for id in v.index]

    nodes = pd.concat(nodes.values(), sort=True)

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


def write_edge_data_to_graph(series, graph_in, var_name=None):
    r"""
    Writes data describing the edges to the graph. Data has to
    be a pd.Series labeled with the (from, to). If the series has
    a name, the data will be stored in the graph under that name.
    If not, `var_name` has to be provided.

    Parameters
    ----------
    series
    graph_in
    var_name

    Returns
    -------

    """
    graph = graph_in.copy()

    assert isinstance(series, pd.Series), \
        "Have to pass a pandas Series."

    if var_name:
        pass
    elif series.name:
        var_name = series.name
    else:
        raise ValueError(r"Have to either pass Series with name or provide var_name.")

    for index, value in series.iteritems():

        graph.edges[index][var_name] = value

    return graph

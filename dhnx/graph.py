# -*- coding: utf-8

"""
This module is designed to hold functions to convert ThermalNetworks into
networkx a graph.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

import pandas as pd
import networkx as nx


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
    nx_graph = nx.MultiDiGraph()  # TODO: Check if this line can be removed.

    pipe_attr = list(thermal_network.components['pipes'].columns)

    pipe_attr.remove('from_node')

    pipe_attr.remove('to_node')

    nx_graph = nx.from_pandas_edgelist(
        thermal_network.components['pipes'],
        'from_node',
        'to_node',
        edge_attr=pipe_attr,
        create_using=thermal_network.graph
    )

    nodes = {
        list_name: thermal_network.components[list_name].copy() for list_name in [
            'consumers',
            'producers',
            'forks'
        ]
    }

    for k, v in nodes.items():
        v.index = [k + '-' + str(id) for id in v.index]

    nodes = pd.concat(nodes.values())

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

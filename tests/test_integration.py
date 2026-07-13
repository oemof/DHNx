# -*- coding: utf-8 -*-
"""
These tests test little examples for the use of the library.

This file is part of project oemof (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/tools/helpers.py

SPDX-License-Identifier: MIT
"""

import os

import networkx as nx
import pandas as pd

import dhnx

from . import helpers

tmpdir = helpers.extend_basic_path("tmp")

basedir = os.path.dirname(__file__)

dir_import_tree = os.path.join(basedir, "_files/tree_network_import")

dir_import_looped = os.path.join(basedir, "_files/looped_network_import")

tree_thermal_network = dhnx.network.ThermalNetwork(dir_import_tree)

looped_thermal_network = dhnx.network.ThermalNetwork(dir_import_looped)

dir_import_invest = os.path.join(basedir, "_files/investment/")

tn_invest = dhnx.network.ThermalNetwork(dir_import_invest + "network")

invest_opt = dhnx.input_output.load_invest_options(
    dir_import_invest + "invest_options"
)

def test_access_attributes():

    network = dhnx.network.ThermalNetwork(dir_import_looped)

    assert isinstance(network.available_components, pd.DataFrame)

    assert network.component_attrs.consumers.id.type == "int"

    assert isinstance(network.components.consumers, pd.DataFrame)

    assert isinstance(network.sequences.producers.temp_inlet, pd.DataFrame)


def test_get_nx_graph():

    nx_graph = looped_thermal_network.to_nx_graph()

    assert isinstance(nx_graph, nx.Graph)

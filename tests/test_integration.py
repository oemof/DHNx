# -*- coding: utf-8 -*-
"""
These tests test little examples for the use of the library.

This file is part of project oemof (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/tools/helpers.py

SPDX-License-Identifier: MIT
"""

import os

import pandas as pd
import networkx as nx

import dhnx
import helpers


tmpdir = helpers.extend_basic_path('tmp')

basedir = os.path.dirname(__file__)

dir_import = os.path.join(basedir, '_files/network_import')


def test_import_export_csv():
    dir_export = os.path.join(tmpdir, 'network_export')

    network = dhnx.network.ThermalNetwork()
    network = network.from_csv_folder(dir_import)

    network.to_csv_folder(dir_export)

    helpers.check_if_csv_dirs_equal(dir_import, dir_export)


def test_access_attributes():

    network = dhnx.network.ThermalNetwork(dir_import)

    assert isinstance(network.available_components, pd.DataFrame)

    assert network.component_attrs.consumers.id.type == 'int'

    assert isinstance(network.components.consumers, pd.DataFrame)

    assert isinstance(network.sequences.edges.temperature_return, pd.DataFrame)


def test_get_nx_graph():
    network = dhnx.network.ThermalNetwork(dir_import)

    nx_graph = network.to_nx_graph()

    assert isinstance(nx_graph, nx.Graph)


def test_static_map():
    thermal_network = dhnx.network.ThermalNetwork(dir_import)

    # plot static map
    dhnx.plotting.StaticMap(thermal_network)


def test_interactive_map():
    # initialize a thermal network
    thermal_network = dhnx.network.ThermalNetwork(dir_import)

    # plot interactive map
    interactive_map = dhnx.plotting.InteractiveMap(thermal_network)
    interactive_map.draw()

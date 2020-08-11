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

thermal_network = dhnx.network.ThermalNetwork(dir_import)

dir_import_invest = os.path.join(basedir, '_files/investment/')

tn_invest = dhnx.network.ThermalNetwork(dir_import_invest + 'network')

invest_opt = dhnx.input_output.load_invest_options(
    dir_import_invest + 'invest_options'
)

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

    nx_graph = thermal_network.to_nx_graph()

    assert isinstance(nx_graph, nx.Graph)


def test_static_map():
    # plot static map
    dhnx.plotting.StaticMap(thermal_network)


def test_interactive_map():
    # plot interactive map
    interactive_map = dhnx.plotting.InteractiveMap(thermal_network)
    interactive_map.draw()


def test_setup_operation_optimization():

    thermal_network.optimize_operation()


def test_setup_investment_optimization():
    
    oemof_dhnx_model = dhnx.optimization.setup_optimise_investment(
        tn_invest, invest_opt)


def test_setup_simulation():

    thermal_network.simulate()

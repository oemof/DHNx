# -*- coding: utf-8 -*-
"""
This is a collection of helper functions which work on their own and can be
used by various classes. If there are too many helper-functions, they will
be sorted in different modules.

This file is part of project oemof (github.com/oemof/oemof). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/tools/helpers.py

SPDX-License-Identifier: MIT
"""

import os

import networkx as nx

import district_heating_simulation as dhs
import helpers


tmpdir = helpers.extend_basic_path('tmp')


def test_import_export_csv():
    basedir = os.path.dirname(__file__)
    dir_import = os.path.join(basedir, '_files/network_import')
    dir_export = os.path.join(tmpdir, 'network_export')

    network = dhs.network.ThermalNetwork()
    network = network.from_csv_folder(dir_import)

    network.to_csv_folder(dir_export)

    helpers.check_if_csv_dirs_equal(dir_import, dir_export)


def test_get_nx_graph():
    basedir = os.path.dirname(__file__)
    dir_import = os.path.join(basedir, '_files/network_import')

    network = dhs.network.ThermalNetwork(dir_import)

    nx_graph = network.to_nx_graph()

    assert isinstance(nx_graph, nx.Graph)


def test_static_map():
    # initialize a thermal network
    thermal_network = dhs.network.ThermalNetwork('data_csv_input')

    # plot static map
    dhs.plotting.StaticMap(thermal_network)


def test_interactive_map():
    # initialize a thermal network
    thermal_network = dhs.network.ThermalNetwork('data_csv_input')

    # plot interactive map
    interactive_map = dhs.plotting.InteractiveMap(thermal_network)
    interactive_map.draw()

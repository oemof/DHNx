# -*- coding: utf-8 -*-
"""
These tests test if proper errors are raised when the data is not consistent, of the
wrong type or not all required data are given.

This file is part of project oemof (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/tools/helpers.py

SPDX-License-Identifier: MIT
"""

import os

import pytest

import dhnx


basedir = os.path.dirname(__file__)

dir_import = os.path.join(basedir, '_files/network_import')

dir_import_inconsistent = os.path.join(basedir, '_files/inconsistent_network_import')

thermal_network = dhnx.network.ThermalNetwork(dir_import)


# TODO: The assertions that let these tests fail have yet to be implemented.
#
# def test_datatype_param_nodes():
#     with pytest.raises(TypeError):
#         thermal_network.producers['id'] = np.float(thermal_network.producers['node_id'])
#
#
# def test_datatype_param_pipes():
#     with pytest.raises(TypeError):
#         thermal_network.pipes['id'] = np.float(thermal_network.pipes['id'])
#
#
# def test_required_param_nodes():
#     with pytest.raises(ValueError):
#         thermal_network.producers = thermal_network.producers.drop('lat', axis=1)
#
#
# def test_required_param_pipes():
#     with pytest.raises(ValueError):
#         thermal_network.pipes = thermal_network.pipes.drop('from_node', axis=1)


def test_load_inconsistent_thermal_network():
    with pytest.raises(ValueError):
        dhnx.network.ThermalNetwork(dir_import_inconsistent)


def test_add():
    # missing required attributes
    with pytest.raises(ValueError):
        thermal_network.add('Pipe', 10)

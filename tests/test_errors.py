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

import copy
import pytest

import dhnx


basedir = os.path.dirname(__file__)

dir_import = os.path.join(basedir, '_files/looped_network_import')

dir_import_inconsistent = os.path.join(basedir, '_files/inconsistent_network_import')

thermal_network = dhnx.network.ThermalNetwork(dir_import)

dir_import_invest = os.path.join(basedir, '_files/investment/')

tn_invest = dhnx.network.ThermalNetwork(dir_import_invest + 'network')

invest_opt = dhnx.input_output.load_invest_options(
    dir_import_invest + 'invest_options'
)


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


def test_prod_prod():
    # there is a direct producer to producer connection
    with pytest.raises(ValueError, match=r"goes from producers to producers."):
        tn_invest_wrong_1 = copy.deepcopy(tn_invest)
        tn_invest_wrong_1.components['pipes'].at[0, 'to_node'] = 'producers-0'
        dhnx.optimization_models.setup_optimise_investment(tn_invest_wrong_1, invest_opt)


def test_cons_cons():
    # there is a edge from consumer to consumer
    with pytest.raises(ValueError, match=r"goes from consumer to consumer"):
        tn_invest_wrong_2 = copy.deepcopy(tn_invest)
        tn_invest_wrong_2.components['pipes'].at[10, 'from_node'] = 'consumers-0'
        dhnx.optimization_models.setup_optimise_investment(tn_invest_wrong_2, invest_opt)


def test_prod_cons():
    # there is a direct producer to consumer connection
    with pytest.raises(ValueError, match=r"goes from producers directly to consumers, or vice "):
        tn_invest_wrong_3 = copy.deepcopy(tn_invest)
        tn_invest_wrong_3.components['pipes'].at[0, 'to_node'] = 'consumers-0'
        dhnx.optimization_models.setup_optimise_investment(tn_invest_wrong_3, invest_opt)

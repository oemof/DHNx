# -*- coding: utf-8 -*-
"""
These tests test little examples for the use of the library.

This file is part of project oemof (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/tools/helpers.py

SPDX-License-Identifier: MIT
"""

import os

import dhnx


basedir = os.path.dirname(__file__)

dir_import = os.path.join(basedir, '_files/looped_network_import')

thermal_network = dhnx.network.ThermalNetwork(dir_import)


def test_add():
    thermal_network.add('Producer', 5, lat=1, lon=1)

    assert thermal_network.components['producers'].loc[5].to_list() == [1., 1., "Producer"]


def test_remove():
    thermal_network.remove('Consumer', 1)

    assert 4 not in thermal_network.components['consumers'].index

# -*- coding: utf-8 -*-
"""
These tests test little examples for the use of the library.

This file is part of project oemof (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/tools/helpers.py

SPDX-License-Identifier: MIT
"""

import os

import numpy as np

import district_heating_simulation as dhs


basedir = os.path.dirname(__file__)

dir_import = os.path.join(basedir, '_files/network_import')

dir_import_inconsistent = os.path.join(basedir, '_files/inconsistent_network_import')

thermal_network = dhs.network.ThermalNetwork(dir_import)


def test_add():
    thermal_network.add('Producer', 5, lat=1, lon=1)

    assert thermal_network.components['producers'].loc[5].to_list() == [1., 1., np.nan]


def test_remove():
    thermal_network.remove('Consumer', 4)

    assert 4 not in thermal_network.components['consumers'].index

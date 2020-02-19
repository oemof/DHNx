# -*- coding: utf-8

"""
This module is designed to hold implementations of simulation models. The
implementation uses oemof/tespy.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

import networkx as nx
import numpy as np
import pandas as pd

from .model import SimulationModel


class SimulationModelTespy(SimulationModel):
    r"""
    Implementation of a simulation model using tespy.
    """
    def __init__(self, thermal_network):
        super().__init__(thermal_network)

    def setup(self):
        pass

    def solve(self):
        pass

    def get_results(self):
        pass


def simulate(thermal_network):
    r"""
    Takes a thermal network and returns the result of
    the simulation.

    Parameters
    ----------
    thermal_network

    Returns
    -------
    results : dict
    """
    model = SimulationModelTespy(thermal_network)

    model.solve()

    results = model.get_results()

    return results

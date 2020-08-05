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
import re

from .model import SimulationModel


class SimulationModelNumpy(SimulationModel):
    r"""
    Implementation of a simulation model using numpy.
    """
    def __init__(self, thermal_network):
        super().__init__(thermal_network)
        self.results = {}

        self.nx_graph = self.thermal_network.to_nx_graph()

    def _setup_hydraulic_eqn(self):

        def _set_producers(m):
            producers = [name for name in m.columns if re.search('producers', name)]

            assert len(producers) == 1, "Currently, only one producer allowed."

            m.loc[:, producers] = - m.loc[:, ~m.columns.isin(producers)].sum(1)

            return m

        inc_mat = nx.incidence_matrix(self.nx_graph, oriented=True).todense()

        consumers_mass_flow = self.thermal_network.sequences.consumers.mass_flow.copy()

        consumers_mass_flow.columns = ['consumers-' + m for m in consumers_mass_flow.columns]

        all_mass_flow = pd.DataFrame(
            0,
            columns=self.nx_graph.nodes(),
            index=self.thermal_network.timeindex
        )

        all_mass_flow.loc[:, consumers_mass_flow.columns] = consumers_mass_flow

        all_mass_flow = _set_producers(all_mass_flow)

        return inc_mat, all_mass_flow

    def _solve_hydraulic_eqn(self, inc_mat, all_mass_flow, tolerance = 1e-10):

        all_mass_flow = np.array(all_mass_flow)

        for t in self.thermal_network.timeindex:

            x, residuals, rank, s = np.linalg.lstsq(inc_mat, all_mass_flow[t], rcond=None)

            assert residuals < tolerance,\
                f"Residuals {residuals} are larger than tolerance {tolerance}!"

            self.results.update({t: x})

        self.results = pd.DataFrame.from_dict(
            self.results,
            orient='index',
            columns=self.nx_graph.edges()
        )

    def _solve_thermal_eqn(self):
        pass

    def setup(self):
        pass

    def solve(self):

        inc_mat, all_mass_flow = self._setup_hydraulic_eqn()

        self._solve_hydraulic_eqn(inc_mat, all_mass_flow)

        self._solve_thermal_eqn()

    def get_results(self):
        return self.results


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
    model = SimulationModelNumpy(thermal_network)

    model.solve()

    results = model.get_results()

    return results

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


class SimulationModelNumpy(SimulationModel):
    r"""
    Implementation of a simulation model using numpy.
    """
    def __init__(self, thermal_network):
        super().__init__(thermal_network)
        self.results = {}

    def _solve_hydraulic_eqn(self, tolerance = 1e-10):
        results = {}

        mass_flow_data = self.thermal_network.sequences.consumers.mass_flow.copy()

        mass_flow_data.columns = ['consumers-' + m for m in mass_flow_data.columns]

        nx_graph = self.thermal_network.to_nx_graph()

        for t in self.thermal_network.timeindex:

            inc_mat = nx.incidence_matrix(nx_graph, oriented=True).todense()

            mass_flow = {key: 0 for key in nx_graph.nodes()}

            mass_flow.update(dict(mass_flow_data.iloc[t]))

            mass_flow = np.array(list(mass_flow.values()))

            mass_flow[0] = - np.sum(mass_flow[1:])

            x, residuals, rank, s = np.linalg.lstsq(inc_mat, mass_flow, rcond=None)

            assert residuals < tolerance,\
                f"Residuals {residuals} are larger than tolerance {tolerance}!"

            results.update({t: x})

        results = pd.DataFrame.from_dict(results, orient='index', columns=nx_graph.edges())

        return results

    def _solve_thermal_eqn(self):
        pass

    def setup(self):
        pass

    def solve(self):
        mass_flows = self._solve_hydraulic_eqn()
        print(mass_flows)
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

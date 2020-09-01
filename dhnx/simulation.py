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
from .helpers import Dict
from .graph import write_edge_data_to_graph


class SimulationModelNumpy(SimulationModel):
    r"""
    Implementation of a simulation model using numpy.
    """
    def __init__(self, thermal_network):
        super().__init__(thermal_network)
        self.results = {}

        self.nx_graph = self.thermal_network.to_nx_graph()

        self.inc_mat = None

        self.input_data = Dict()

    def _concat_sequences(self, name):

        select_sequences = [
            d[name].copy().rename(columns=lambda x: component + '-' + x)
            for component, d in self.thermal_network.sequences.items()
            if name in d
        ]

        concat_sequences = pd.concat(select_sequences, 1)

        return concat_sequences

    def _prepare_hydraulic_eqn(self):

        def _set_producers(m):
            producers = [name for name in m.columns if re.search('producers', name)]

            assert len(producers) == 1, "Currently, only one producer allowed."

            m.loc[:, producers] = - m.loc[:, ~m.columns.isin(producers)].sum(1)

            return m

        self.inc_mat = nx.incidence_matrix(self.nx_graph, oriented=True).todense()

        mass_flow = pd.DataFrame(
            0,
            columns=self.nx_graph.nodes(),
            index=self.thermal_network.timeindex
        )

        input_data = self._concat_sequences('mass_flow')

        mass_flow.loc[:, input_data.columns] = input_data

        self.input_data.mass_flow = _set_producers(mass_flow)

    def _solve_hydraulic_eqn(self, tolerance=1e-10):

        edges_mass_flow = {}

        for t in self.thermal_network.timeindex:

            x, residuals, rank, s = np.linalg.lstsq(
                self.inc_mat,
                self.input_data.mass_flow.loc[t, :],
                rcond=None
            )

            assert residuals < tolerance,\
                f"Residuals {residuals} are larger than tolerance {tolerance}!"

            edges_mass_flow.update({t: x})

        self.results['edges-mass_flow'] = pd.DataFrame.from_dict(
            edges_mass_flow,
            orient='index',
            columns=self.nx_graph.edges()
        )

        # TODO: Calculate these
        # 'edges-pressure_losses'
        # NOTE: edges have distributed and localized pressure losses zeta_dis * L/D**5
        # nodes-pressure_losses
        # NOTE: nodes have only localized pressure losses
        # 'global-pressure_losses'
        # 'producers-pump_power'

        self.results['edges-pressure_losses'] = None

        self.results['nodes-pressure_losses'] = None

        self.results['producers-pump_power'] = None  # pressure losses times mass flow for one loop

    def _prepare_thermal_eqn(self):

        self.temp_inlet = pd.DataFrame(
            0,
            columns=self.nx_graph.nodes(),
            index=self.thermal_network.timeindex
        )

        input_data = self._concat_sequences('temp_inlet')

        self.temp_inlet.loc[:, input_data.columns] = input_data

    def _solve_thermal_eqn(self):

        c = 4190  # TODO: set heat capacity

        heat_transfer_coefficient = nx.adjacency_matrix(
            self.nx_graph, weight='heat_transfer_coefficient_W/mK').todense()

        diameter = 1e-3 * nx.adjacency_matrix(self.nx_graph, weight='diameter_mm').todense()

        length = nx.adjacency_matrix(self.nx_graph, weight='length_m').todense()

        exponent_constant = - np.pi\
                   * np.multiply(heat_transfer_coefficient, np.multiply(diameter, length))\
                   / c  # TODO: Check units

        def _calc_temps(exponent_constant, known_temp, direction):
            # TODO: Rethink function layout and naming

            temps = {}

            for t in self.thermal_network.timeindex:

                # Divide exponent matrix by current edges-mass_flows.
                data = self.results['edges-mass_flow'].loc[t, :].copy()

                data = 1/data

                graph_with_data = write_edge_data_to_graph(
                    data, self.nx_graph, var_name='edges-mass_flow'
                )

                inverse_mass_flows = nx.adjacency_matrix(
                    graph_with_data, weight='edges-mass_flow'
                ).todense()

                exponent = np.multiply(exponent_constant, inverse_mass_flows)

                matrix = np.exp(exponent)

                # Clear out elements where matrix was zero before exponentiation. This could be
                # replaced by properly passing `where` to np.multiply in the line above.
                matrix = np.multiply(matrix, nx.adjacency_matrix(self.nx_graph).todense())

                # Adapt matrix
                if direction == 1:
                    matrix = matrix.T
                    normalisation = np.array(nx.adjacency_matrix(self.nx_graph).sum(0)).flatten()

                    normalisation = np.divide(np.array([1]), normalisation, where=normalisation!=0)

                elif direction == -1:
                    normalisation = np.array(nx.adjacency_matrix(self.nx_graph).sum(1)).flatten()

                    normalisation = np.divide(np.array([1]), normalisation, where=normalisation!=0)

                else:
                    raise ValueError("Direction has to be either 1 or -1.")

                normalisation = np.diag(normalisation)

                matrix = np.dot(normalisation, matrix)

                matrix = np.identity(matrix.shape[0]) - matrix

                vector = np.array(known_temp.loc[t])

                x, residuals, rank, s = np.linalg.lstsq(
                    matrix,
                    vector,
                    rcond=None
                )

                temps.update({t: x})

            temp_df = pd.DataFrame.from_dict(
                temps,
                orient='index',
                columns=self.nx_graph.nodes()
            )

            return temp_df

        temp_inlet = _calc_temps(exponent_constant, self.temp_inlet, direction=1)

        def _set_temp_return_input(temp_inlet):

            temp_return = pd.DataFrame(
                0,
                columns=self.nx_graph.nodes(),
                index=self.thermal_network.timeindex
            )

            temp_drop = self._concat_sequences('temperature_drop')

            temp_return.loc[:, temp_drop.columns] = temp_inlet.loc[:, temp_drop.columns] - temp_drop

            return temp_return

        temp_return_known = _set_temp_return_input(temp_inlet)

        temp_return = _calc_temps(exponent_constant, temp_return_known, direction=-1)

        # TODO: Calculate these
        # 'edges-heat_losses'
        # 'global-heat_losses'

        self.results['nodes-temp_inlet'] = temp_inlet

        self.results['nodes-temp_return'] = temp_return

        self.results['edges-heat_losses'] = None

        self.results['global-heat_losses'] = None

    def prepare(self):

        self._prepare_hydraulic_eqn()

        self._prepare_thermal_eqn()


    def solve(self):

        self._solve_hydraulic_eqn()

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

    model.prepare()

    model.solve()

    results = model.get_results()

    return results

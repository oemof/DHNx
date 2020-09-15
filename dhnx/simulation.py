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
    def __init__(self, thermal_network, rho=971.78, c=4190, mu=0.00035):
        super().__init__(thermal_network)
        self.results = {}

        self.nx_graph = self.thermal_network.to_nx_graph()

        assert nx.algorithms.tree.is_tree(self.nx_graph),\
            "Currently, only tree networks can be modeled. " \
            "Looped networks are not implemented yet."

        self.inc_mat = None

        self.input_data = Dict()

        self.rho = rho  # kg/m3

        self.c = c  # J/(kg*K)

        self.mu = mu  # kg/(m*s)

        self.temp_env = 20

    def _concat_sequences(self, name):
        r"""
        Concatenates sequences of all
        components with a given variable name

        Parameters
        ----------
        name : str
            Name of the variable

        Returns
        -------
        concat_sequences : pd.DataFrame
            DataFrame containing the sequences

        """
        select_sequences = [
            d[name].copy().rename(columns=lambda x: component + '-' + x)
            for component, d in self.thermal_network.sequences.items()
            if name in d
        ]

        concat_sequences = pd.concat(select_sequences, 1)

        return concat_sequences

    def _prepare_hydraulic_eqn(self):

        def _set_producers_mass_flow(m):
            r"""
            Set the mass flow of the producer.

            Parameters
            ----------
            m : pd.DataFrame
                DataFrame with all know consumer mass flows.

            Returns
            -------
            m : pd.DataFrame
                DataFrame with all know mass flow of
                consumers and producer.
            """
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

        self.input_data.mass_flow = _set_producers_mass_flow(mass_flow)

    def _solve_hydraulic_eqn(self, tolerance=1e-10):

        pipes_mass_flow = {}

        for t in self.thermal_network.timeindex:

            x, residuals, rank, s = np.linalg.lstsq(
                self.inc_mat,
                self.input_data.mass_flow.loc[t, :],
                rcond=None
            )

            assert residuals < tolerance,\
                f"Residuals {residuals} are larger than tolerance {tolerance}!"

            pipes_mass_flow.update({t: x})

        self.results['pipes-mass_flow'] = pd.DataFrame.from_dict(
            pipes_mass_flow,
            orient='index',
            columns=self.nx_graph.edges()
        )

        self.results['pipes-mass_flow'].columns.names = ('from_node', 'to_node')

        # TODO: Calculate these
        # 'pipes-pressure_losses'
        # NOTE: pipes have distributed and localized pressure losses zeta_dis * L/D**5
        # nodes-pressure_losses
        # NOTE: nodes have only localized pressure losses
        # 'global-pressure_losses'
        # 'producers-pump_power'

        def _calculate_reynolds():
            r"""
            Calculates the reynolds number.

            ..math::

                Re = \frac{4\dot{m}{\pi\mu D}

            Returns
            -------

            re : pd.DataFrame
            """
            pipes_mass_flow = self.results['pipes-mass_flow']

            diameter = self.thermal_network.components.pipes[['from_node', 'to_node', 'diameter_mm']]

            diameter = 1e-3 * diameter.set_index(['from_node', 'to_node'])['diameter_mm']

            re = 4 * pipes_mass_flow.divide(diameter, axis='columns') \
                / (np.pi * self.mu)

            return re

        def _calculate_lambda(re):
            r"""
            Calculates the darcy friction factor.

            ..math::

                \lambda = 0.007 \cdot Re^{-0.13} \cdot D ^ {-0.14}

            Parameters
            ----------
            re

            Returns
            -------

            lamb : pd.DataFrame
            """

            factor_diameter = self.thermal_network.components.pipes[
                ['from_node', 'to_node', 'diameter_mm']
            ]

            factor_diameter =  (1e-3 \
                * factor_diameter.set_index(['from_node', 'to_node'])['diameter_mm']) ** -0.14

            lamb = 0.07 * re ** -0.13

            lamb = lamb.multiply(factor_diameter, axis='columns')

            return lamb

        def _calculate_pipes_pressure_losses(lamb):
            r"""
            Calculates the pressure losses in the pipes.

            .. math::

            \delta p = \lambda \frac{8L}{\rho \pi^2 D^5}\dot{m}^2.

            Parameters
            ----------
            lamb : pd.DataFrame
                DataFrame with lambda values for each timestep.

            Returns
            -------
            pipes_pressure_losses : pd.DataFrame
                DataFrame with pressure losses values for each timestep.
            """
            pipes_mass_flow = self.results['pipes-mass_flow'].copy()

            constant = 8 * lamb / (self.rho * np.pi**2)

            length = self.thermal_network.components.pipes[['from_node', 'to_node', 'length_m']]

            diameter = self.thermal_network.components.pipes[['from_node', 'to_node', 'diameter_mm']]

            length = length.set_index(['from_node', 'to_node'])['length_m']

            diameter = diameter.set_index(['from_node', 'to_node'])['diameter_mm']

            diameter_5 = 1e-3 * diameter ** 5

            pipes_pressure_losses = constant * pipes_mass_flow\
                .multiply(length, axis='columns')\
                .divide(diameter_5, axis='columns')

            return pipes_pressure_losses

        def _calculate_nodes_pressure_losses():
            r"""
            Calculates localized pressure losses at the nodes.

            \Delta p_{loc} = \zeta
            Returns
            -------
            nodes_pressure_losses : pd.DataFrame
                Pressure losses at the nodes.
            """
            constant = 8 / (self.rho * np.pi ** 2)

            zeta_nodes = 2  # TODO: use zeta values from input data

            diameter_4 = self.thermal_network.components.pipes[
                ['from_node', 'to_node', 'diameter_mm']
            ]

            diameter_4 = diameter_4.set_index(['from_node', 'to_node'])['diameter_mm']

            diameter_4 = (1e-3 * diameter_4) ** 4

            def _get_inflow_nodes(pipes_mass_flow, t):
                # TODO: Avoid passing t here.

                flow_into_node = np.sign(pipes_mass_flow).reset_index()

                flow_into_node.loc[flow_into_node[t] < 0, 'flow_into_node'] = flow_into_node[
                    'from_node']

                flow_into_node.loc[flow_into_node[t] > 0, 'flow_into_node'] = flow_into_node[
                    'to_node']

                flow_into_node.drop(t, axis=1, inplace=True)

                flow_into_node.set_index(['from_node', 'to_node'], inplace=True)

                return flow_into_node

            nodes_pressure_losses = {}

            for t in self.thermal_network.timeindex:

                pipes_mass_flow = self.results['pipes-mass_flow'].loc[t, :]

                mass_flow_2_over_diameter_4 = pipes_mass_flow.divide(diameter_4)

                mass_flow_2_over_diameter_4.name = 'mass_flow_2_over_diameter_4'

                inflow_nodes = _get_inflow_nodes(pipes_mass_flow, t)

                mass_flow_2_over_diameter_4_nodes = pd.concat([mass_flow_2_over_diameter_4, inflow_nodes], axis=1)

                mass_flow_2_over_diameter_4_nodes = mass_flow_2_over_diameter_4_nodes \
                    .set_index(inflow_nodes['flow_into_node'], drop=True) \
                    .loc[:, 'mass_flow_2_over_diameter_4']

                x = constant * zeta_nodes * mass_flow_2_over_diameter_4_nodes

                nodes_pressure_losses.update({t: x})

            nodes_pressure_losses = pd.DataFrame.from_dict(nodes_pressure_losses, orient='index')
            print(nodes_pressure_losses)
            import sys
            sys.exit()
            return nodes_pressure_losses

        re = _calculate_reynolds()

        lamb = _calculate_lambda(re)

        pipes_pressure_losses = _calculate_pipes_pressure_losses(lamb)

        nodes_pressure_losses = _calculate_nodes_pressure_losses()

        self.results['pipes-pressure_losses'] = pipes_pressure_losses

        self.results['nodes-pressure_losses'] = nodes_pressure_losses

        self.results['global-pressure_losses'] = nodes_pressure_losses

        self.results['producers-pump_power'] = None  # pressure losses times mass flow for one loop

    def _prepare_thermal_eqn(self):

        self.input_data.temp_inlet = pd.DataFrame(
            0,
            columns=self.nx_graph.nodes(),
            index=self.thermal_network.timeindex
        )

        input_data = self._concat_sequences('temp_inlet')

        self.input_data.temp_inlet.loc[:, input_data.columns] = input_data

    def _solve_thermal_eqn(self):

        heat_transfer_coefficient = nx.adjacency_matrix(
            self.nx_graph, weight='heat_transfer_coefficient_W/mK').todense()

        diameter = 1e-3 * nx.adjacency_matrix(self.nx_graph, weight='diameter_mm').todense()

        length = nx.adjacency_matrix(self.nx_graph, weight='length_m').todense()

        exponent_constant = - np.pi\
                   * np.multiply(heat_transfer_coefficient, np.multiply(diameter, length))\
                   / self.c  # TODO: Check units

        def _calc_temps(exponent_constant, known_temp, direction):
            r"""
            Calculate temperatures

            .. math::

            \Delta T = exp ^(\frac{U \pi D L }{c}) \cdot exp ^{1}{\dot{m}} \Delta T_{known}

            Parameters
            ----------
            exponent_constant : np.array
                Constant part of the exponent.

            known_temp : pd.DataFrame
                Known temperatures at producers or consumers.

            direction : +1 or -1
                For inlet and return flow.

            Returns
            -------
            temp_df : pd.DataFrame
                DataFrame containing temperatures for all nodes.
            """
            # TODO: Rethink function layout and naming

            temps = {}

            for t in self.thermal_network.timeindex:

                # Divide exponent matrix by current pipes-mass_flows.
                data = self.results['pipes-mass_flow'].loc[t, :].copy()

                data = 1/data

                graph_with_data = write_edge_data_to_graph(
                    data, self.nx_graph, var_name='pipes-mass_flow'
                )

                inverse_mass_flows = nx.adjacency_matrix(
                    graph_with_data, weight='pipes-mass_flow'
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

                vector[vector!=0] -= self.temp_env

                x, residuals, rank, s = np.linalg.lstsq(
                    matrix,
                    vector,
                    rcond=None
                )

                temps.update({t: x + self.temp_env})

            temp_df = pd.DataFrame.from_dict(
                temps,
                orient='index',
                columns=self.nx_graph.nodes()
            )

            return temp_df

        temp_inlet = _calc_temps(exponent_constant, self.input_data.temp_inlet, direction=1)

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

        def _calculate_pipes_heat_losses(temp_node):

            pipes_heat_losses = {}

            for i, row in temp_inlet.iterrows():

                mass_flow = self.results['pipes-mass_flow'].loc[i, :].copy()

                temp_difference = np.array(np.dot(row, self.inc_mat)).flatten()

                heat_losses = mass_flow

                pipes_heat_losses[i] = self.c * heat_losses.multiply(temp_difference, axis=0)

            pipes_heat_losses = pd.DataFrame.from_dict(pipes_heat_losses, orient='index')

            return pipes_heat_losses

        pipes_heat_losses = _calculate_pipes_heat_losses(temp_inlet) \
                            + _calculate_pipes_heat_losses(temp_return)

        global_heat_losses = pipes_heat_losses.sum(axis=1)

        global_heat_losses.name = 'global_heat_losses'

        self.results['nodes-temp_inlet'] = temp_inlet

        self.results['nodes-temp_return'] = temp_return

        self.results['pipes-heat_losses'] = pipes_heat_losses

        self.results['global-heat_losses'] = global_heat_losses

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

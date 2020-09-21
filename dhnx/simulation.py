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
import warnings

from .model import SimulationModel
from .helpers import Dict
from .graph import write_edge_data_to_graph
from .input_output import save_results


idx = pd.IndexSlice


class SimulationModelNumpy(SimulationModel):
    r"""
    Implementation of a simulation model using numpy.
    """
    def __init__(self, thermal_network, rho=971.78, c=4190, mu=0.00035):
        super().__init__(thermal_network)
        self.results = {}

        self.nx_graph = thermal_network.to_nx_graph()

        assert nx.algorithms.tree.is_tree(self.nx_graph),\
            "Currently, only tree networks can be modeled. " \
            "Looped networks are not implemented yet."

        self.inc_mat = nx.incidence_matrix(self.nx_graph, oriented=True).todense()

        self.input_data = Dict()

        self.rho = rho  # kg/m3

        self.c = c  # J/(kg*K)

        self.mu = mu  # kg/(m*s)

        self.temp_env = thermal_network.sequences.environment.temp_env.iloc[:, 0]

        if self._concat_scalars('height') is not None:
            warnings.warn(
                "Pressure differences due to height differences are not implemented yet."
            )

    def _concat_scalars(self, name):
        r"""
        Concatenates scalars of all components with a given variable name

        Parameters
        ----------
        name : str
            Name of the variable

        Returns
        -------
        concat_sequences : pd.DataFrame
            DataFrame containing the sequences
        """
        select_scalars = [
            scalar[name].copy().rename(index=lambda x: component + '-' + str(x))
            for component, scalar in self.thermal_network.components.items()
            if name in scalar
        ]

        if select_scalars:
            select_scalars = pd.concat(select_scalars, 0)

            return select_scalars

        else:
            return None

    def _concat_sequences(self, name):
        r"""
        Concatenates sequences of all components with a given variable name

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
        r"""
        Prepares the input data for the hydraulic problem.
        """

        def _set_producers_mass_flow(m):
            r"""
            Sets the mass flow of the producer.

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

        self.input_data.mass_flow = pd.DataFrame(
            0,
            columns=self.nx_graph.nodes(),
            index=self.thermal_network.timeindex
        )

        input_data = self._concat_sequences('mass_flow')

        self.input_data.mass_flow.loc[:, input_data.columns] = input_data

        self.input_data.mass_flow = _set_producers_mass_flow(self.input_data.mass_flow)

    def _solve_hydraulic_eqn(self, tolerance=1e-10):
        r"""
        Solves the hydraulic problem.
        """

        def _calculate_pipes_mass_flow():
            r"""
            Determines the mass flow in all pipes using numpy's
            least squares function.

            Returns
            -------
            pipes_mass_flow : pd.DataFrame
                Mass flow in the pipes
            """

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

            pipes_mass_flow = pd.DataFrame.from_dict(
                pipes_mass_flow,
                orient='index',
                columns=self.nx_graph.edges()
            )

            pipes_mass_flow.columns.names = ('from_node', 'to_node')

            return pipes_mass_flow

        def _calculate_reynolds():
            r"""
            Calculates the Reynolds number.

            ..math::

                Re = \frac{4\dot{m}}{\pi\mu D}

            Returns
            -------
            re : pd.DataFrame
                Reynoldes number for every timestep and pipe.
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

                \lambda = 0.007 \cdot Re ^ {-0.13} \cdot D ^ {-0.14}

            Parameters
            ----------
            re : pd.DataFrame
                Reynoldes number for every timestep and pipe.

            Returns
            -------
            lamb : pd.DataFrame
                Darcy friction factor for every timestep and pipe.
            """

            factor_diameter = self.thermal_network.components.pipes[
                ['from_node', 'to_node', 'diameter_mm']
            ]

            factor_diameter =  (1e-3 \
                * factor_diameter.set_index(['from_node', 'to_node'])['diameter_mm']) ** -0.14

            lamb = 0.07 * re ** -0.13

            lamb = lamb.multiply(factor_diameter, axis='columns')

            return lamb

        def _calculate_pipes_distributed_pressure_losses(lamb):
            r"""
            Calculates the pressure losses in the pipes.

            .. math::

                \delta p = \lambda \frac{8L}{\rho \pi^2 D^5}\dot{m}^2.

            Parameters
            ----------
            lamb : pd.DataFrame
                Darcy friction factor for every timestep and pipe.

            Returns
            -------
            pipes_pressure_losses : pd.DataFrame
                DataFrame with distributed pressure losses for every timestep and pipe.
            """
            pipes_mass_flow = self.results['pipes-mass_flow'].copy()

            pipes_mass_flow_2 = pipes_mass_flow ** 2

            constant = 8 * lamb / (self.rho * np.pi**2)

            length = self.thermal_network.components.pipes[['from_node', 'to_node', 'length_m']]

            diameter = self.thermal_network.components.pipes[['from_node', 'to_node', 'diameter_mm']]

            length = length.set_index(['from_node', 'to_node'])['length_m']

            diameter = diameter.set_index(['from_node', 'to_node'])['diameter_mm']

            diameter_5 = (1e-3 * diameter) ** 5

            pipes_pressure_losses = constant * pipes_mass_flow_2\
                .multiply(length, axis='columns')\
                .divide(diameter_5, axis='columns')

            return pipes_pressure_losses

        def _calculate_pipes_localized_pressure_losses():
            r"""
            Calculates localized pressure losses at the nodes.

            .. math::

                \Delta p_{loc} = \frac{8\zeta\dot{m}^2}{\rho \pi^2 D^4}

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

            pipes_localized_pressure_losses = {}

            for t in self.thermal_network.timeindex:

                pipes_mass_flow = self.results['pipes-mass_flow'].loc[t, :]

                mass_flow_2 = pipes_mass_flow ** 2

                mass_flow_2_over_diameter_4 = mass_flow_2.divide(diameter_4)

                mass_flow_2_over_diameter_4.name = 'mass_flow_2_over_diameter_4'

                x = constant * zeta_nodes * mass_flow_2_over_diameter_4

                pipes_localized_pressure_losses.update({t: x})

            pipes_localized_pressure_losses = pd.DataFrame.from_dict(
                pipes_localized_pressure_losses,
                orient='index'
            )

            return pipes_localized_pressure_losses

        def _calculate_global_pressure_losses(pipes_pressure_losses):

            def calculate_path_weights(source_nodes, sink_nodes, graph, weight):

                path_weights = {}

                for sink in sink_nodes:
                    for source in source_nodes:

                        path_weights[sink] = nx.dijkstra_path_length(
                            graph,
                            source=source,
                            target=sink,
                            weight=weight
                        )

                return path_weights

            def _calculate_paths_pressure_losses():

                sink_nodes = [node for node, data in self.nx_graph.nodes(data=True) if
                              data['node_type'] == 'consumer']

                source_nodes = [node for node, data in self.nx_graph.nodes(data=True) if
                                data['node_type'] == 'producer']

                paths_pressure_losses = {}

                for t in self.thermal_network.timeindex:

                    graph = write_edge_data_to_graph(
                        pipes_pressure_losses.loc[t, :],
                        self.nx_graph,
                        var_name='pipes_pressure_losses'
                    )

                    path_weights = calculate_path_weights(
                        source_nodes,
                        sink_nodes,
                        graph,
                        'pipes_pressure_losses'
                    )

                    paths_pressure_losses[t] = path_weights

                paths_pressure_losses = pd.DataFrame.from_dict(paths_pressure_losses, orient='index')

                return paths_pressure_losses

            paths_pressure_losses = _calculate_paths_pressure_losses()

            # Here, we take the path with the maximum pressure losses and assume that the other
            # consumer's valves are adjusted so that in sum, the pressure losses along all paths are
            # equal. We multiply by the factor of two to represent the pressure losses along inlet
            # and return flow.

            global_pressure_losses = 2 * paths_pressure_losses.max(axis=1)

            return global_pressure_losses

        def _calculate_pump_power(global_pressure_losses):

            eta_pump = 1

            producers = [
                node for node, data in self.nx_graph.nodes(data=True)
                if data['node_type'] == 'producer'
            ]

            mass_flow_producers = \
                self.results['pipes-mass_flow'].loc[:, idx[producers, :]].sum(axis=1)

            pump_power = mass_flow_producers * global_pressure_losses / (eta_pump * self.rho)

            return pump_power

        self.results['pipes-mass_flow'] = _calculate_pipes_mass_flow()

        re = _calculate_reynolds()

        lamb = _calculate_lambda(re)

        pipes_dist_pressure_losses = _calculate_pipes_distributed_pressure_losses(lamb)

        pipes_loc_pressure_losses = _calculate_pipes_localized_pressure_losses()

        pipes_total_pressure_losses = pipes_dist_pressure_losses + pipes_loc_pressure_losses

        global_pressure_losses = _calculate_global_pressure_losses(pipes_total_pressure_losses)

        pump_power = _calculate_pump_power(global_pressure_losses)

        self.results['pipes-dist_pressure_losses'] = pipes_dist_pressure_losses

        self.results['pipes_loc_pressure_losses'] = pipes_loc_pressure_losses

        self.results['global-pressure_losses'] = global_pressure_losses

        self.results['producers-pump_power'] = pump_power

    def _prepare_thermal_eqn(self):
        r"""
        Prepares the input data for the thermal problem.
        """

        self.input_data.temp_inlet = pd.DataFrame(
            0,
            columns=self.nx_graph.nodes(),
            index=self.thermal_network.timeindex
        )

        input_data = self._concat_sequences('temp_inlet')

        self.input_data.temp_inlet.loc[:, input_data.columns] = input_data

    def _solve_thermal_eqn(self):
        r"""
        Solves the thermal problem.
        """

        def _calculate_exponent_constant():
            r"""
            Calculates the constant part of the exponent that determines the
            cooling of the medium in the pipes.

            .. math::

                \frac{- U \pi D L }{c}

            Returns
            -------
            exponent_constant : np.matrix
                Constant part of the exponent
            """

            heat_transfer_coefficient = nx.adjacency_matrix(
                self.nx_graph, weight='heat_transfer_coefficient_W/mK').todense()

            diameter = 1e-3 * nx.adjacency_matrix(self.nx_graph, weight='diameter_mm').todense()

            length = nx.adjacency_matrix(self.nx_graph, weight='length_m').todense()

            exponent_constant = - np.pi\
                       * np.multiply(heat_transfer_coefficient, np.multiply(diameter, length))\
                       / self.c

            return exponent_constant

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

                vector[vector!=0] -= self.temp_env.loc[t]

                x, residuals, rank, s = np.linalg.lstsq(
                    matrix,
                    vector,
                    rcond=None
                )

                temps.update({t: x + self.temp_env.loc[t]})

            temp_df = pd.DataFrame.from_dict(
                temps,
                orient='index',
                columns=self.nx_graph.nodes()
            )

            return temp_df

        def _set_temp_return_input(temp_inlet):
            r"""
            Sets the temperature of the return pipes
            at the consumers.

            T_{cons,r} = T_{cons,i} - T_{cons,drop}

            Parameters
            ----------
            temp_inlet : pd.DataFrame
                Known inlet temperature

            Returns
            -------
            temp_return : pd.DataFrame
                Return temperature with the consumers values set.
            """

            temp_return = pd.DataFrame(
                0,
                columns=self.nx_graph.nodes(),
                index=self.thermal_network.timeindex
            )

            temp_drop = self._concat_sequences('temperature_drop')

            temp_return.loc[:, temp_drop.columns] = temp_inlet.loc[:, temp_drop.columns] - temp_drop

            return temp_return

        def _calculate_pipes_heat_losses(temp_node):
            r"""
            Calculates the pipes' heat losses given the
            temperatures.

            Parameters
            ----------
            temp_node : pd.DataFrame
                Temperatures at the nodes.

            Returns
            -------
            pipes_heat_losses : pd.DataFrame
                Heat losses in the pipes.
            """

            pipes_heat_losses = {}

            for i, row in temp_node.iterrows():

                mass_flow = self.results['pipes-mass_flow'].loc[i, :].copy()

                temp_difference = np.abs(np.array(np.dot(row, self.inc_mat)).flatten())

                pipes_heat_losses[i] = self.c * mass_flow.multiply(temp_difference, axis=0)

            pipes_heat_losses = pd.DataFrame.from_dict(pipes_heat_losses, orient='index')

            return pipes_heat_losses

        exponent_constant = _calculate_exponent_constant()

        temp_inlet = _calc_temps(exponent_constant, self.input_data.temp_inlet, direction=1)

        temp_return_known = _set_temp_return_input(temp_inlet)

        temp_return = _calc_temps(exponent_constant, temp_return_known, direction=-1)

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


def simulate(thermal_network, results_dir=None):
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

    if results_dir is not None:
        save_results(results, results_dir)

    return results

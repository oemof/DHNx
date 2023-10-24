# -*- coding: utf-8

"""
This module is designed to hold the definition of the central ThermalNetwork
object and its components.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

import os

import networkx as nx
import pandas as pd

from .graph import thermal_network_to_nx_graph
from .helpers import Dict
from .input_output import CSVNetworkExporter
from .input_output import CSVNetworkImporter
from .input_output import load_component_attrs
from .optimization.optimization_models import optimize_operation
from .optimization.optimization_models import setup_optimise_investment
from .optimization.optimization_models import solve_optimisation_investment
from .simulation import simulate

dir_name = os.path.dirname(__file__)

available_components = pd.read_csv(os.path.join(dir_name, 'components.csv'), index_col=0)

component_attrs = load_component_attrs(os.path.join(dir_name, 'component_attrs'),
                                       available_components)

required_attrs = {
    list_name: [
        attr for attr, specs in attrs.items() if specs.requirement == 'required'
    ] for list_name, attrs in component_attrs.items()
}

default_attrs = {
    list_name: {
        attr: specs.default for attr, specs in attrs.items()
        if not pd.isnull(specs.default)
    } for list_name, attrs in component_attrs.items()
}


class ThermalNetwork():
    r"""
    Class representing thermal (heating/cooling) networks.

    Parameters
    ----------
    availalable_components
    component_attrs
    components
    sequences
    results
    graph

    Examples
    --------
    >>> from dhnx.network import ThermalNetwork
    >>> tnw = ThermalNetwork()
    >>> tnw.is_consistent()
    True
    """
    def __init__(self, dirname=None):

        self.available_components = available_components
        self.component_attrs = component_attrs
        self.components = Dict({key: pd.DataFrame() for key in available_components.list_name})
        self.sequences = Dict()
        self.results = Dict()
        self.timeindex = None
        self.graph = None

        if dirname is not None:
            try:
                self.from_csv_folder(dirname)

            except ImportError:
                print('Failed to import file.')

    def __repr__(self):
        r"""
        This method defines what is returned if you perform print() or str()
        on a ThermalNetwork.
        """
        summary = ''
        for component, data in self.components.items():
            count = len(data)
            if count > 0:
                summary += ' * ' + str(count) + ' ' + component + '\n'

        if summary == '':
            return "Empty dhnx.network.ThermalNetwork object containing no components."

        return f"dhnx.network.ThermalNetwork object with these components\n{summary}"

    def from_csv_folder(self, dirname):
        importer = CSVNetworkImporter(self, dirname)

        self = importer.load()

        return self

    def to_csv_folder(self, dirname):
        exporter = CSVNetworkExporter(self, dirname)

        exporter.save()

    def to_nx_graph(self):
        nx_graph = thermal_network_to_nx_graph(
            self, type_of_graph=nx.DiGraph(),
        )

        return nx_graph

    def to_nx_undirected_graph(self):
        nx_graph = thermal_network_to_nx_graph(
            self, type_of_graph=nx.Graph(),
        )

        return nx_graph

    def set_defaults(self):
        r"""
        Sets default values on component DataFrames.

        Returns
        -------
        None
        """

        for component, data in self.components.items():
            for default_name, default_value in default_attrs[component].items():

                data[default_name] = default_value

    def add(self, class_name, id, **kwargs):
        r"""
        Adds a row with id to the component DataFrame specified by class_name.

        Parameters
        ----------
        class_name
        id
        kwargs
        """
        assert class_name in available_components.index, \
            f"Component class {class_name} is not within the available components" \
            f" {available_components.index}."

        list_name = available_components.loc[class_name].list_name

        assert id not in self.components[list_name].index, \
            f"There is already a component with the id {id}."

        # check if required parameters are in kwargs
        missing_required = list(set(required_attrs[list_name]) - kwargs.keys())

        missing_required.remove('id')

        if bool(missing_required):
            raise ValueError(f"Required attributes {missing_required} are not given")

        # if not defined in kwargs, set default attributes
        component_data = default_attrs[list_name].copy()

        component_data.update(kwargs)

        # add to component DataFrame
        for key, value in component_data.items():
            self.components[list_name].loc[id, key] = value

    def remove(self, class_name, id):
        r"""
        Removes the row with id from the component DataFrame specified by class_name.

        Parameters
        ----------
        class_name : str
            Name of the component class
        id : int
            id of the component to remove
        """
        assert class_name in available_components.index, \
            "Component class '{}' is not within the available_components."

        list_name = available_components.loc[class_name].list_name

        assert id in self.components[list_name].index, \
            f"There is no component with the id {id}."

        self.components[list_name].drop(id, inplace=True)

    def is_consistent(self):
        r"""
        Checks that
         * pipes connect to existing nodes,
         * pipes do not connect a node with itself,
         * there are no duplicate pipes between two nodes.
        """
        nodes = {list_name: self.components[list_name].copy() for list_name in [
            'consumers',
            'producers',
            'forks'
        ]}

        for k, v in nodes.items():
            v.index = [k + '-' + str(id) for id in v.index]

        nodes = pd.concat(nodes.values(), sort=True)

        node_indices = nodes.index

        for id, data in self.components.pipes.iterrows():

            if not data['from_node'] in node_indices:
                raise ValueError(f"Node {data['from_node']} not defined.")

            if not data['to_node'] in node_indices:
                raise ValueError(f"Node {data['to_node']} not defined.")

            assert data['from_node'] != data['to_node'], \
                f"Pipe {id} connects {data['from_node']} to itself"

        if not self.components.pipes.empty:

            duplicate_pipes = [
                name for name, group in self.components.pipes.groupby(['from_node', 'to_node'])
                if len(group) > 1
            ]

            assert not duplicate_pipes, (
                f"There is more than one pipe that connects "
                f"{[pipe[0] + ' to ' + pipe[1] for pipe in duplicate_pipes]}")

        return True

    def _list_nested_dict_values(self, d):
        r"""
        Unwraps a nested dict and returns a list of all
        values in the branches of the dictionary.

        Parameters
        ----------
        d : dict
            Nested dictionary

        Returns
        -------
        leaves : list
            List of all values
        """
        leaves = []
        for _, v in d.items():
            if isinstance(v, dict):
                leaves.extend(self._list_nested_dict_values(v))
            else:
                leaves.append(v)
        return leaves

    @staticmethod
    def _are_indices_equal(indices):
        r"""
        Compares a list of pd.Index's and asserts
        that they are equal.

        Parameters
        ----------
        indices : list
            List containing pd.Index

        Returns
        -------
        True
        """
        if len(indices) == 1:
            print("Only one sequence given. Need more than one time-index to compare.")
            return True

        for index in indices[1:]:
            assert indices[0].equals(index)

        return True

    def set_timeindex(self):
        r"""
        Takes all sequences and checks if their timeindex is identical.
        If that is the case, it sets the timeindex attribute of the
        class.
        If there are no sequences given, the timeindex will keep the default value.
        """
        sequence_dfs = self._list_nested_dict_values(self.sequences)

        if sequence_dfs:

            indices = [df.index for df in sequence_dfs]

            self._are_indices_equal(indices)

            self.timeindex = indices[0]

        else:
            print("No sequences found to create timeindex from")

    def reproject(self, crs):
        pass

    def optimize_operation(self):
        self.results.operation = optimize_operation(self)

    def optimize_investment(
            self, pipeline_invest_options,
            additional_invest_options=None, **kwargs):
        """

        Parameters
        ----------
        pipeline_invest_options : pandas.DataFrame
            Table with the investment options for the district heating
            pipelines.
            The table requires the columns:
            - "":
            - "":
            - "":
            - "":
        additional_invest_options : dict
            Optional dictionary with pandas.DataFrame with additional
            oemof-solph components for the consumers and the producers.
        kwargs

        Returns
        -------

        """

        oemof_opti_model = setup_optimise_investment(
            self,
            pipeline_invest_options,
            additional_invest_options=additional_invest_options,
            **kwargs
        )

        self.results.optimization = solve_optimisation_investment(
            oemof_opti_model
        )

        return self.results.optimization

    def simulate(self, *args, **kwargs):
        self.results.simulation = simulate(self, *args, **kwargs)

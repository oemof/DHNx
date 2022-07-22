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

import pandas as pd
import geopandas as gpd

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
        nx_graph = thermal_network_to_nx_graph(self)

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
        assert class_name in available_components.index,\
            f"Component class {class_name} is not within the available components" \
            f" {available_components.index}."

        list_name = available_components.loc[class_name].list_name

        assert id not in self.components[list_name].index,\
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
        assert class_name in available_components.index,\
            "Component class '{}' is not within the available_components."

        list_name = available_components.loc[class_name].list_name

        assert id in self.components[list_name].index,\
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

    def optimize_investment(self, invest_options, **kwargs):

        oemof_opti_model = setup_optimise_investment(
            self, invest_options, **kwargs
        )

        self.results.optimization = solve_optimisation_investment(
            oemof_opti_model
        )

    def simulate(self, *args, **kwargs):
        self.results.simulation = simulate(self, *args, **kwargs)

    def aggregate(self, maxlength = 100):
        """
        :param maxlength:
        :return:
        """
        self.aggregatednetwork = dict()
        test_dict = aggregation(forks = self.components["forks"],
                                pipes = self.components["pipes"],
                                consumers = self.components["consumers"],
                                producers = self.components["producers"])

# TODO: Länge der Superpipes berechnen
# TODO: Leistungsabhängige Aggregation
# TODO: Straßen werden als ganzes aggregiert, obwohl das nicht immer sinnvoll ist (siehe Straße "Im Grund" oben rechts)

def aggregation(forks, pipes, consumers, producers):

    from shapely import geometry, ops
    import geopandas as gpd
    import matplotlib.pyplot as plt
    import pandas as pd

# TODO: Warnings anschalten
    import warnings
    warnings.filterwarnings("ignore")

    # # # Identifizierung der Superforks
    # DL und GL aus pipes speichern
    DLGLpipes = pipes.loc[pipes['type'].isin(['DL', 'GL'])]

    # Anzahl von Verbindungen von den forks zählen (from_node und to_node)
    count_forks_from_node = DLGLpipes['from_node'].value_counts()
    count_forks_to_node = DLGLpipes['to_node'].value_counts()

    # Anzahl von from_node und to_node addieren
    count_forks = count_forks_from_node.add(count_forks_to_node, fill_value=0)

    # Die Superforks, also forks mit 1, 3, 4 Verbindungen, identifizieren
    count_superforks = count_forks[count_forks.isin([1, 3, 4])]

    # Index von den Superforks speichern
    superforks_indexlist = count_superforks.index.tolist()

    # Superforks aus forks nehmen, wenn die forks als Superfork identifiziert wurden
    super_forks = forks.copy()
    super_forks = super_forks[super_forks['id_full'].isin(superforks_indexlist)]
    super_forks = super_forks.reset_index(drop=True)

    # Anzahl der Verbindungen
    # super_forks['Verbindungen'] = count_superforks.tolist() #Fehler, weil producer-0 in count_superforks drin ist und nicht in super_forks


    # # # 2. SuperPipes identifizieren und mergen

    # super_pipes initialisieren
    super_pipes = pipes.copy()
    super_pipes = super_pipes.drop(range(0, len(pipes)))
    # Liste für aggregierte forks und pipes initialisieren
    aggregated_forks = []
    aggregated_pipes = []
    # TODO: Stopp bei producer! --> beseitigt durch neue abfrage, diese nochmal überprüfen
    i = -1  # # # Erste Schleife: Superforks durchgehen

    while i <= len(super_forks) - 2:  # länge ist absolut und id startet bei 0
        i += 1
        # Den aktuellen super_fork (i) aus der super_fork Liste auswählen ...
        superfork_i_id_full = super_forks.loc[i]['id_full']
        # ... und zu den aggregierten hinzugügen
        aggregated_forks.append(superfork_i_id_full)
        # Pipes die am Superfork i verbunden sind raus suchen und in einen GeoDataFrame speichern
        pipes_superfork_i_from_node = DLGLpipes[DLGLpipes['from_node'] == superfork_i_id_full]
        pipes_superfork_i_to_node = DLGLpipes[DLGLpipes['to_node'] == superfork_i_id_full]
        pipes_superfork_i = pipes_superfork_i_from_node.append(pipes_superfork_i_to_node)
        pipes_superfork_i = pipes_superfork_i.reset_index(drop=True)

        a = - 1 # # # Zweite Schleife: Superpipes a vom Superfork i durchgehen
        while a <= len(pipes_superfork_i) - 2:  # länge ist absolut und id startet bei 0
            a += 1
            # Wenn die pipe schon aggregiert wurde, soll die nächst pipe überprüft werden
            if pipes_superfork_i.loc[a]['id'] in aggregated_pipes:
                continue  # evtl. a += 1 vorher break oder continue
            # Ein Segment ist die Anreihung von pipes bevor diese gemerget werden
            # Das Segment wird initialisiert und die pipe a ist die erste pipe des Segments
            segment_i_a = pipes_superfork_i.copy()
            segment_i_a = segment_i_a[segment_i_a.index == a]
            segment_i_a = segment_i_a.reset_index(drop=True)

            aggregation_segment = False # # # Dritte Schleife: Die Elemente b von pipe a durchgehen
            b = 0
            while aggregation_segment == False:

                # print('Superfork i: ', superfork_i_id_full)
                # print('pipe a: ', segment_i_a.at[0, 'id'])
                # print('segment b: ', b)

                # Heraussuchen des nächsten forks der mit der pipe b verbunden ist
                fork_from_pipe_b_segment_i_a = 0  # evtl nicht nötig
                fork_to_pipe_b_segment_i_a = 0  # evtl nicht nötig
                fork_from_pipe_b_segment_i_a = segment_i_a.at[b, 'from_node']  # hier tritt ein fehler auf
                fork_to_pipe_b_segment_i_a = segment_i_a.at[b, 'to_node']
                count_type_forks_pipe_b_segment_i_a = 0
                status_fork_from_pipe_b_segment_i_a = 0  # nicht benötigt
                status_fork_to_pipe_b_segment_i_a = 0  # nicht benötigt
                # Initialisieren des nächsten forks
                fork_next_segment_i_a = 0
                # TODO: Kann der nächste Fork überhaupt in aggregated forks sein, wenn die pipe nicht aggregiert ist?
                # Prüfen ob der fork 'from' bereits aggregiert oder ein superfork ist oder ein producer ist
                # Wenn ja wird die Anzahl der count_type_forks_pipe_b_segment_i_a erhöht ...
                # ... falls nicht ist der fork zum nächsten segment der fork 'from'
                if fork_from_pipe_b_segment_i_a in super_forks[
                    'id_full'].unique() or fork_from_pipe_b_segment_i_a in aggregated_forks or fork_from_pipe_b_segment_i_a in \
                        producers['id_full'].unique():
                    count_type_forks_pipe_b_segment_i_a += 1
                    status_fork_from_pipe_b_segment_i_a = 'aggregated/superfork'  # nicht benötigt
                else:
                    fork_next_segment_i_a = fork_from_pipe_b_segment_i_a  # Der nächste fork darf noch nicht aggregiert sein
                # Prüfen ob der fork 'to' bereits aggregiert oder ein superfork ist oder ein producer ist
                # Wenn ja wird die Anzahl der count_type_forks_pipe_b_segment_i_a erhöht
                # ... falls nicht ist der fork zum nächsten segment der fork 'to'
                if fork_to_pipe_b_segment_i_a in super_forks[
                    'id_full'].unique() or fork_to_pipe_b_segment_i_a in aggregated_forks or fork_to_pipe_b_segment_i_a in \
                        producers['id_full'].unique():
                    count_type_forks_pipe_b_segment_i_a += 1
                    status_fork_to_pipe_b_segment_i_a = 'aggregated/superfork'  # nicht benötigt
                else:
                    fork_next_segment_i_a = fork_to_pipe_b_segment_i_a  # Der nächste fork darf noch nicht aggregiert sein
                # Wenn beide forks aggregiert sind wird das Segment gemergt
                if count_type_forks_pipe_b_segment_i_a == 2:
                    # merge new geometry
                    geom_multi_segment_i_a = geometry.MultiLineString(segment_i_a['geometry'].unique())
                    geom_line_segment_i_a = ops.linemerge(geom_multi_segment_i_a)
                    # create new pipe
                    merged_segment_i_a = segment_i_a[segment_i_a.index == 0]
                    merged_segment_i_a['geometry'] = geom_line_segment_i_a
                    #
                    merged_segment_i_a['to_node'] = segment_i_a.loc[b]['to_node']
                    # add new pipe to super pipes
                    super_pipes = super_pipes.append(merged_segment_i_a)
                    # add pipe_ids to aggregated pipes
                    aggregated_pipes = aggregated_pipes + segment_i_a['id'].tolist()

                    aggregation_segment == True
                    # TODO: Länge des Segments berechnen und to node from node anpassen

                    break


                    # Identifizieren welche pipes mit fork_next_segment_i_a verbunden sind
                elif count_type_forks_pipe_b_segment_i_a == 1:  #

                    pipe_next_segment_i_a = 0  #
                    # Nächste Pipe darf nicht die aktuelle sein!
                    # TODO: Von einigen Forks gehen zwei pipes hin oder zwei pipes weg. Daher andere Überprüfung nötig!
                    # TODO:EVTL from und to in ein Array und dann die pipe die nicht die letzte ist als neue
                    # TODO:Abfrage schlauer gestalten

                    list_of_connected_pipes_to_next_fork = []
                    list_of_connected_pipes_to_next_fork = list_of_connected_pipes_to_next_fork + DLGLpipes.loc[
                        DLGLpipes['from_node'].isin([fork_next_segment_i_a])]['id'].tolist() + DLGLpipes.loc[
                                                               DLGLpipes['to_node'].isin([fork_next_segment_i_a])][
                                                               'id'].tolist()

                    #print('list of connected pipes: ', list_of_connected_pipes_to_next_fork)

                    if segment_i_a.at[b, 'id'] == list_of_connected_pipes_to_next_fork[0]:
                        pipe_next_segment_i_a = DLGLpipes.loc[
                            DLGLpipes['id'].isin([list_of_connected_pipes_to_next_fork[1]])]

                    elif segment_i_a.at[b, 'id'] == list_of_connected_pipes_to_next_fork[1]:
                        pipe_next_segment_i_a = DLGLpipes.loc[
                            DLGLpipes['id'].isin([list_of_connected_pipes_to_next_fork[0]])]

                    else:
                        print('error: next fork doesnt connect to any new pipe')

                    # b hoch zählen
                    b += 1

                    # hinzufügen zu segment i_a
                    segment_i_a = segment_i_a.append(pipe_next_segment_i_a)

                    # index resetten
                    segment_i_a = segment_i_a.reset_index(drop=True)

                    # fork zu aggregated fork
                    aggregated_forks.append(fork_next_segment_i_a)


                else:
                    print('error: pipe is not connected to any aggregated fork or super fork')

    # Länge der super_pipes berechnen
    super_pipes['length'] = super_pipes.length

    print('list of aggregated pipes: ', aggregated_pipes)
    print('list of aggregated forks: ', aggregated_forks)

    # plotten
    _, ax = plt.subplots()
    super_pipes.plot(ax=ax, color='red')
    # consumers.plot(ax=ax, color='green')
    producers.plot(ax=ax, color='blue')
    super_forks.plot(ax=ax, color='grey')
    plt.title('Geometry after aggregation of pipes')
    plt.show()

    # Exportieren als geojson
    super_forks.to_file('super_forks.geojson', driver='GeoJSON')
    super_pipes.to_file('super_pipes.geojson', driver='GeoJSON')


    # return
    return {
        'super_forks': super_forks,
        'super_consumers': consumers, # not yet defined
        'super_producers': producers, # not yet defined
        'super_pipes': super_pipes,
    }


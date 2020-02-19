# -*- coding: utf-8

"""
This module is designed to hold importers and exporters to different file formats.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

import logging
import os

from addict import Dict
import pandas as pd


logger = logging.getLogger()


class NetworkImporter():
    r"""
    Generic Importer object for network.ThermalNetwork
    """
    def __init__(self, thermal_network, basedir):
        thermal_network.is_consistent()
        self.thermal_network = thermal_network
        self.basedir = basedir

    def load(self):
        pass


class NetworkExporter():
    r"""
    Generic Exporter object for network.ThermalNetwork
    """
    def __init__(self, thermal_network, basedir):
        thermal_network.is_consistent()
        self.thermal_network = thermal_network
        self.basedir = basedir

    def save(self):
        pass


class CSVNetworkImporter(NetworkImporter):
    r"""
    Imports thermal networks from directory with csv-files.
    """
    def load_component_table(self, list_name):

        if list_name not in self.thermal_network.available_components.list_name.values:
            raise KeyError(f"Component '{list_name}'is not "
                           f"part of the available components.")

        file_name = list_name + '.csv'
        component_table = pd.read_csv(os.path.join(self.basedir, file_name), index_col=0)

        return component_table

    def load_sequence(self, list_name, attr_name):

        if list_name not in self.thermal_network.available_components.list_name.values:
            raise KeyError(f"Component '{list_name}' is not "
                           f"part of the available components.")

        if attr_name not in self.thermal_network.component_attrs:
            logger.info("Attribute '%s' is not "
                        "part of the component attributes.", attr_name)

        file_name = '-'.join([list_name, attr_name]) + '.csv'
        sequence = pd.read_csv(os.path.join(self.basedir, 'sequences', file_name), index_col=0)

        return sequence

    def load(self):
        for name in os.listdir(self.basedir):

            if name.endswith('.csv'):

                list_name = os.path.splitext(name)[0]

                self.thermal_network.components[list_name] = self.load_component_table(list_name)

            elif os.path.isdir(os.path.join(self.basedir, name)):

                assert name in ['sequences'], f"Unknown directory name. Directory '{name}' " \
                                              f"is not a defined subdirectory."

                for sequence_name in os.listdir(os.path.join(self.basedir, name)):

                    assert sequence_name.endswith('.csv'), f"Inappropriate filetype of '{name}'" \
                                                           f"for csv import."

                    list_name, attr_name = tuple(sequence_name.split('-'))

                    attr_name = os.path.splitext(attr_name)[0]

                    if list_name not in self.thermal_network.sequences:
                        self.thermal_network.sequences[list_name] = Dict()

                    self.thermal_network.sequences[list_name][attr_name] =\
                        self.load_sequence(list_name, attr_name)

            else:
                raise ImportError(f"Inappropriate filetype of '{name}' for csv import.")

        self.thermal_network.is_consistent()

        return self.thermal_network


class CSVNetworkExporter(NetworkExporter):
    r"""
    Exports thermal networks to directory with csv-files.
    """
    def __init__(self, thermal_network, basedir):
        super().__init__(thermal_network, basedir)
        if not os.path.exists(self.basedir):
            os.mkdir(self.basedir)

    def save_component_table(self, component_table, name):
        component_table.to_csv(os.path.join(self.basedir, name))

    def save_sequence(self, list_name, attr_name, sequence):

        sequence_dir = os.path.join(self.basedir, 'sequences')

        if not os.path.exists(sequence_dir):

            os.mkdir(sequence_dir)

        file_name = '-'.join([list_name, attr_name]) + '.csv'

        sequence.to_csv(os.path.join(self.basedir, 'sequences', file_name))

    def save(self):
        for list_name, component_table in self.thermal_network.components.items():
            if not component_table.empty:
                filename = list_name + '.csv'
                self.save_component_table(component_table, filename)

        for list_name, subdict in self.thermal_network.sequences.items():

            for attr_name, sequence in subdict.items():

                self.save_sequence(list_name, attr_name, sequence)


class OSMNetworkImporter(NetworkImporter):
    r"""
    Imports thermal networks from OSM data.

    Not yet implemented.
    """


class GDFNetworkExporter(NetworkExporter):
    r"""
    Exports thermal networks to geopandas.GeoDataFrame.

    Not yet implemented.
    """


def load_component_attrs(dir_name, available_components):

    component_attrs = {}

    for file_name in os.listdir(dir_name):

        list_name = os.path.splitext(file_name)[0]

        assert list_name in available_components.list_name.values, f"Unknown component {list_name}"\
                                                                   " not in available components."

        df = pd.read_csv(os.path.join(dir_name, file_name), index_col=0)

        component_attrs[list_name] = df.T.to_dict()

    return Dict(component_attrs)

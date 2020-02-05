import os
import pandas as pd


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
    def __init__(self, thermal_network, basedir):
        super().__init__(thermal_network, basedir)

    def load_component_table(self, name, index_col):
        component_table = pd.read_csv(os.path.join(self.basedir, name), index_col=index_col)

        return component_table

    def load(self):
        self.thermal_network.producers = self.load_component_table('producers.csv', 'node_id')

        self.thermal_network.consumers = self.load_component_table('consumers.csv', 'node_id')

        self.thermal_network.forks = self.load_component_table('forks.csv', 'node_id')

        self.thermal_network.edges = self.load_component_table('edges.csv', 'edge_id')

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

    def save(self):
        self.save_component_table(self.thermal_network.producers, 'producers.csv')

        self.save_component_table(self.thermal_network.consumers, 'consumers.csv')

        self.save_component_table(self.thermal_network.forks, 'forks.csv')

        self.save_component_table(self.thermal_network.edges, 'edges.csv')


class OSMNetworkImporter(NetworkImporter):
    r"""
    Imports thermal networks from OSM data.
    """
    def __init__(self):
        pass


class GDFNetworkExporter(NetworkExporter):
    r"""
    Exports thermal networks to geopandas.GeoDataFrame.
    """
    def __init__(self):
        pass

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

    def get_producers(self):
        producers = pd.read_csv(os.path.join(self.basedir, 'producers.csv'), index_col='node_id')
        return producers

    def get_consumers(self):
        consumers = pd.read_csv(os.path.join(self.basedir, 'consumers.csv'), index_col='node_id')
        return consumers

    def get_splits(self):
        splits = pd.read_csv(os.path.join(self.basedir, 'splits.csv'), index_col='node_id')
        return splits

    def get_edges(self):
        edges = pd.read_csv(os.path.join(self.basedir, 'edges.csv'), index_col='edge_id')
        return edges

    def load(self):
        self.thermal_network.producers = self.get_producers()

        self.thermal_network.consumers = self.get_consumers()

        self.thermal_network.forks = self.get_splits()

        self.thermal_network.edges = self.get_edges()

        return self.thermal_network


class CSVNetworkExporter(NetworkExporter):
    r"""
    Exports thermal networks to directory with csv-files.
    """
    def __init__(self, thermal_network, basedir):
        super().__init__(thermal_network, basedir)
        if not os.path.exists(self.basedir):
            os.mkdir(self.basedir)

    def save_producers(self, producers):
        producers.to_csv(os.path.join(self.basedir, 'producers.csv'))
        return producers

    def save_consumers(self, consumers):
        consumers.to_csv(os.path.join(self.basedir, 'consumers.csv'))
        return consumers

    def save_splits(self, splits):
        splits.to_csv(os.path.join(self.basedir, 'splits.csv'))
        return splits

    def save_edges(self, edges):
        edges.to_csv(os.path.join(self.basedir, 'edges.csv'))
        return edges

    def save(self):
        pass


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


def load_problem(dir):
    problem = {}

    for filename in os.listdir(dir):
        name = filename.strip('.csv')
        problem[name] = pd.read_csv(os.path.join(dir, filename))

    return problem

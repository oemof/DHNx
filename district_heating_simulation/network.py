import networkx as nx
from .input_output import ImportCSV, ExportCSV


class ThermalNetwork():
    r"""
    Class representing thermal (heating/cooling) networks.
    """
    def _init__(self, filename):
        self.producers = None
        self.splits = None
        self.consumers = None
        self.edges = None
        self.results = None
        self.units = None
        self.graph = None

    def load_from_csv(self, dirname):
        importer = ImportCSV(dirname)

        self.producers = importer.get_producers()
        self.splits = importer.get_splits()
        self.consumers = importer.get_consumers()
        self.edges = importer.get_edges()

    def save_to_csv(self, dirname):
        exporter = ExportCSV(dirname)

        exporter.save_producers(self.producers)
        exporter.save_splits(self.splits)
        exporter.save_consumers(self.consumers)
        exporter.save_edges(self.edges)

    def set_units(self):
        return self.units

    def convert_to_nx_graph(self):
        return self.graph

    def reproject(self, crs):
        pass


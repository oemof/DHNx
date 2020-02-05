import pandas as pd

from .input_output import CSVNetworkImporter, CSVNetworkExporter
from .graph import thermal_network_to_nx_graph


class ThermalNetwork():
    r"""
    Class representing thermal (heating/cooling) networks.

    Parameters
    ----------

    Examples
    --------
    >>> from district_heating_simulation import ThermalNetwork
    >>> tnw = ThermalNetwork('csv_folder')
    >>> tnw.is_consistent()
    True
    """
    def __init__(self, dirname=None):

        if dirname is not None:
            try:
                self.from_csv_folder(dirname)
                self.results = None
                self.units = {}
                self.graph = None

            except ImportError:
                print('Failed to import file.')

        else:
            self.producers = ProducerTable()
            self.consumers = ConsumerTable()
            self.forks = ForkTable()
            self.edges = EdgeTable()
            self.results = None
            self.units = {}
            self.graph = None

    def from_csv_folder(self, dirname):
        importer = CSVNetworkImporter(self, dirname)

        self = importer.load()

        return self

    def to_csv_folder(self, dirname):
        exporter = CSVNetworkExporter(self, dirname)

        self = exporter.save()

    def to_nx_graph(self):
        nx_graph = thermal_network_to_nx_graph(self)

        return nx_graph

    def set_units(self):
        return self.units

    def is_consistent(self):
        pass

    def reproject(self, crs):
        pass


class NodeTable:
    def __init__(self):
        self.df = pd.DataFrame()


class EdgeTable:
    def __init__(self):
        self.df = pd.DataFrame()


class ProducerTable(NodeTable):
    def __init__(self):
        super().__init__()


class ConsumerTable(NodeTable):
    def __init__(self):
        super().__init__()


class ForkTable(NodeTable):
    def __init__(self):
        super().__init__()

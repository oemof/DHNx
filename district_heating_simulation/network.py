import os

import networkx as nx
import pandas as pd
from .input_output import CSVNetworkImporter, CSVNetworkExporter


class ThermalNetwork():
    r"""
    Class representing thermal (heating/cooling) networks.
    """
    def __init__(self, dirname=None):
        self.producers = None
        self.splits = None
        self.consumers = None
        self.edges = None
        self.nodes = None
        self.results = None
        self.units = {}
        self.graph = None

        if dirname is not None:
            if os.listdir(dirname)[0].endswith('.csv'):
                self.load_from_csv(dirname)
            else:
                ImportError('Failed to import file.')
        else:
            pass

    def load_from_csv(self, dirname):
        importer = CSVNetworkImporter(dirname)

        self.producers = importer.get_producers()
        self.splits = importer.get_splits()
        self.consumers = importer.get_consumers()
        self.edges = importer.get_edges()
        self.nodes = pd.concat([self.producers,
                                self.consumers,
                                self.splits])
        return self

    def save_to_csv(self, dirname):
        exporter = CSVNetworkExporter(dirname)

        exporter.save_producers(self.producers)
        exporter.save_splits(self.splits)
        exporter.save_consumers(self.consumers)
        exporter.save_edges(self.edges)

    def set_units(self):
        return self.units

    def get_nx_graph(self):
        self.graph = nx.MultiDiGraph()

        edge_attr = list(self.edges.columns)
        edge_attr.remove('from_node')
        edge_attr.remove('to_node')

        self.graph = nx.from_pandas_edgelist(
            self.edges,
            'from_node',
            'to_node',
            edge_attr=edge_attr,
            create_using=self.graph
        )

        nodes = pd.concat([self.producers, self.consumers, self.splits], axis=0)
        node_attrs = {node_id: dict(data) for node_id, data in nodes.iterrows()}
        nx.set_node_attributes(self.graph, node_attrs)

        return self.graph

    def reproject(self, crs):
        pass

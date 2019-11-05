import os
import networkx as nx
import pandas as pd
import numpy as np
from shapely.geometry import Point
from shapely.geometry import LineString
import time
import geopandas as gpd


class ImportCSV():
    r"""
    Imports thermal networks from csv files.

    """
    def __init__(self, dirname):
        self.dirname = dirname

    def get_producers(self):
        producers = pd.read_csv(os.path.join(self.dirname, 'producers.csv'), index_col='node_id')
        return producers

    def get_consumers(self):
        consumers = pd.read_csv(os.path.join(self.dirname, 'consumers.csv'), index_col='node_id')
        return consumers

    def get_splits(self):
        splits = pd.read_csv(os.path.join(self.dirname, 'splits.csv'), index_col='node_id')
        return splits

    def get_edges(self):
        edges = pd.read_csv(os.path.join(self.dirname, 'edges.csv'), index_col='edge_id')
        return edges


class ExportCSV():
    r"""
    Exports thermal networks to csv files.

    """
    def __init__(self, dirname):
        self.dirname = dirname
        if not os.path.exists(self.dirname):
            os.mkdir(self.dirname)

    def save_producers(self, producers):
        producers.to_csv(os.path.join(self.dirname, 'producers.csv'))
        return producers

    def save_consumers(self, consumers):
        consumers.to_csv(os.path.join(self.dirname, 'consumers.csv'))
        return consumers

    def save_splits(self, splits):
        splits.to_csv(os.path.join(self.dirname, 'splits.csv'))
        return splits

    def save_edges(self, edges):
        edges.to_csv(os.path.join(self.dirname, 'edges.csv'))
        return edges

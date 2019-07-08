import networkx as nx
import pandas as pd
import numpy as np
from shapely.geometry import Point
from shapely.geometry import LineString
import time
import geopandas as gpd


class ImportExportCSV():
    r"""
    Imports/Exports thermal networks from csv files.
    """
    def __init(self):
        pass

    def load_from_csv(self, filename):
        thermal_network = []
        return thermal_network

    def save_to_csv(self, thermal_network, filename):
        return filename


def create_network(edge_list, node_list):
    r"""
    Create DHN from lists decribing edges and nodes
    """
    G = nx.MultiDiGraph()

    edge_attr = ['lenght_m', 'diameter_mm', 'heat_transfer_coefficient_W/mK', 'roughness_mm']
    G = nx.from_pandas_edgelist(edge_list, 'from_node', 'to_node', edge_attr=edge_attr, create_using=G)

    for node in G.nodes:
        G.add_node(node, lon=node_list.loc[int(node)]['lon'],
                         lat=node_list.loc[int(node)]['lat'],
                         node_type=node_list.loc[int(node)]['node_type'])

    return G

def graph_to_gdfs(G, nodes=True, edges=True, node_geometry=True, fill_edge_geometry=True):
    r"""
    Convert a graph into node and/or edge GeoDataFrames

    Parameters
    ----------
    G : networkx multidigraph
    nodes : bool
        if True, convert graph nodes to a GeoDataFrame and return it
    edges : bool
        if True, convert graph edges to a GeoDataFrame and return it
    node_geometry : bool
        if True, create a geometry column from node x and y data
    fill_edge_geometry : bool
        if True, fill in missing edge geometry fields using origin and
        destination nodes

    Returns
    -------
    GeoDataFrame or tuple
        gdf_nodes or gdf_edges or both as a tuple
    """

    if not (nodes or edges):
        raise ValueError('You must request nodes or edges, or both.')

    to_return = []

    if nodes:

        start_time = time.time()

        nodes = {node:data for node, data in G.nodes(data=True)}
        gdf_nodes = gpd.GeoDataFrame(nodes).T
        if node_geometry:
            gdf_nodes['geometry'] = gdf_nodes.apply(lambda row: Point(row['x'], row['y']), axis=1)
        gdf_nodes.crs = G.graph['crs']
        gdf_nodes.gdf_name = '{}_nodes'.format(G.graph['name'])

        to_return.append(gdf_nodes)
        
    if edges:

        start_time = time.time()

        # create a list to hold our edges, then loop through each edge in the
        # graph
        edges = []
        for u, v, data in G.edges(data=True):
            # for each edge, add key and all attributes in data dict to the
            # edge_details
            edge_details = {'u':u, 'v':v}
            for attr_key in data:
                edge_details[attr_key] = data[attr_key]

            # if edge doesn't already have a geometry attribute, create one now
            # if fill_edge_geometry==True
            if 'geometry' not in data:
                if fill_edge_geometry:
                    point_u = Point((G.nodes[u]['x'], G.nodes[u]['y']))
                    point_v = Point((G.nodes[v]['x'], G.nodes[v]['y']))
                    edge_details['geometry'] = LineString([point_u, point_v])
                else:
                    edge_details['geometry'] = np.nan

            edges.append(edge_details)

        # create a GeoDataFrame from the list of edges and set the CRS
        gdf_edges = gpd.GeoDataFrame(edges)
        gdf_edges.crs = G.graph['crs']
        gdf_edges.gdf_name = '{}_edges'.format(G.graph['name'])

        to_return.append(gdf_edges)
        
    if len(to_return) > 1:
        return tuple(to_return)
    else:
        return to_return[0]

def to_edge_list(G):
    edge_list = nx.to_pandas_edgelist(G, source='from_node', target='to_node')
    edge_list = edge_list[['from_node', 'to_node', 'lenght_m', 'diameter_mm', 'heat_transfer_coefficient_W/mK', 'roughness_mm']]
    edge_list.index.name = 'pipe_no'

    return edge_list

def to_node_list(G):
    nodelist = G.nodes(data=True)
    nodes = [n for n, d in nodelist]
    all_keys = set().union(*(d.keys() for n, d in nodelist))
    node_attr = {k: [d.get(k, float("nan")) for n, d in nodelist] for k in all_keys}
    nodelistdict = {'node_id': nodes}
    nodelistdict.update(node_attr)
    node_list = pd.DataFrame(nodelistdict)
    node_list = node_list.set_index('node_id')
    node_list = node_list[['lat', 'lon', 'node_type']]

    return node_list


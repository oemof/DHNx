# -*- coding: utf-8

"""
This module is designed to hold functions for importing networks and building
footprints from openstreetmap.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

try:
    import geopandas as gpd

except ImportError:
    print("Need to install geopandas to process osm data.")

import pandas as pd

try:
    from shapely.geometry import LineString
    from shapely.ops import nearest_points

except ImportError:
    print("Need to install shapely to download from osm.")


def connect_points_to_network(points, nodes, edges):
    r"""

    Parameter
    ---------
    points :  geopandas.GeoDataFrame
        Points to connect to the network

    nodes : geopandas.GeoDataFrame
        Nodes of the network

    edges : geopandas.GeoDataFrame
        Edges of the network

    Returns
    -------
    points : geopandas.GeoDataFrame
        Points connected to the network

    nodes : geopandas.GeoDataFrame
        Original nodes of the network and
        nearest connecting points on the
        network's edges.

    edges :  geopandas.GeoDataFrame
        Edges of the network.
    """
    edges_united = edges.unary_union

    len_nodes = len(nodes)
    len_points = len(points)

    # assign ids to new points
    n_points = []
    n_nearest_points = []
    n_edges = []

    for i, point in enumerate(points.geometry):
        id_nearest_point = len_nodes + i

        id_point = len_nodes + len_points + i

        nearest_point = nearest_points(edges_united, point)[0]

        n_points.append([id_point, point])

        n_nearest_points.append([id_nearest_point, nearest_point])

        n_edges.append([id_point, id_nearest_point, LineString([point, nearest_point])])

    n_points = gpd.GeoDataFrame(
        n_points,
        columns=['index', 'geometry']).set_index('index')

    n_nearest_points = gpd.GeoDataFrame(
        n_nearest_points,
        columns=['index', 'geometry']).set_index('index')

    n_edges = gpd.GeoDataFrame(n_edges, columns=['u', 'v', 'geometry'])

    joined_nodes = pd.concat([nodes, n_nearest_points], sort=True)
    joined_edges = pd.concat([edges, n_edges], sort=True)

    return n_points, joined_nodes, joined_edges

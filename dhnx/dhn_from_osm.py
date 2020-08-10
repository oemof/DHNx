# -*- coding: utf-8

"""
This module is designed to hold functions for importing networks and building
footprints from openstreetmap.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

import geopandas as gpd
import pandas as pd

from shapely.ops import nearest_points
from shapely.geometry import LineString


def connect_points_to_network(points, nodes, pipes):
    r"""

    Parameter
    ---------
    points :  geopandas.GeoDataFrame
        Points to connect to the network

    nodes : geopandas.GeoDataFrame
        Nodes of the network

    pipes : geopandas.GeoDataFrame
        Pipes of the network

    Returns
    -------
    points : geopandas.GeoDataFrame
        Points connected to the network

    nodes : geopandas.GeoDataFrame
        Nodes of the network

    Pipes :  geopandas.GeoDataFrame
        Pipes of the network.
    """
    pipes_united = pipes.unary_union

    len_nodes = len(nodes)
    len_points = len(points)

    # assign ids to new points
    n_points = []
    n_nearest_points = []
    n_pipes = []

    for i, point in enumerate(points.geometry):
        id_nearest_point = len_nodes + i

        id_point = len_nodes + len_points + i

        nearest_point = nearest_points(pipes_united, point)[0]

        n_points.append([id_point, point.x, point.y, point])

        n_nearest_points.append([id_nearest_point, nearest_point.x, nearest_point.y, nearest_point])

        n_pipes.append([id_point, id_nearest_point, LineString([point, nearest_point])])

    n_points = gpd.GeoDataFrame(
        n_points,
        columns=['index', 'x', 'y', 'geometry']).set_index('index')

    n_nearest_points = gpd.GeoDataFrame(
        n_nearest_points,
        columns=['index', 'x', 'y', 'geometry']).set_index('index')

    n_pipes = gpd.GeoDataFrame(n_pipes, columns=['u', 'v', 'geometry'])

    joined_nodes = pd.concat([nodes, n_nearest_points], sort=True)
    joined_pipes = pd.concat([pipes, n_pipes], sort=True)

    return n_points, joined_nodes, joined_pipes

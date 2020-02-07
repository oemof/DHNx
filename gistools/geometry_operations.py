# -*- coding: utf-8 -*-

"""
General description
-------------------
Some functions for connect_points application.


Copyright (c) 2019 Johannes Röder <johannes.roeder@uni-bremen.de>

SPDX-License-Identifier: GPL-3.0-or-later
"""
__copyright__ = "Johannes Röder <johannes.roeder@uni-bremen.de>"
__license__ = "GPLv3"


import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt


def create_nodes(lines):
    """
    :param lines: geopandas.DataFrame with LineStrings of distribution
                        lines
    :return:    nodes: geopandas.DataFrames containing all nodes of Line-Layer
                    with an identifier column 'K123';
                lines: return line dataframe of input with new columns
                    'id_start' and 'id_end' holding the ids of the nodes of
                    start-point and end-point of line;
    """

    nodes = gpd.GeoDataFrame()

    for i, r in lines.iterrows():
        line_str = lines.iloc[i]['geometry']

        if line_str.type == 'MultiLineString':
            line_str = line_str[0]

        p_0 = Point(line_str.coords[0])
        p_1 = Point(line_str.coords[1])
        nodes = nodes.append({'geometry': p_0}, ignore_index=True)
        nodes = nodes.append({'geometry': p_1}, ignore_index=True)

    # drop duplicates
    # length before deleting douples
    length_1 = len(nodes)
    # transform geometry into wkt
    nodes["geometry"] = nodes["geometry"].apply(lambda geom: geom.wkt)
    # drop duplicates of geometry column
    nodes = nodes.drop_duplicates(["geometry"])
    # create shapely geometry again
    nodes["geometry"] = nodes["geometry"].apply(
        lambda geom: wkt.loads(geom))
    # reset index
    nodes = nodes.reset_index(drop=True)
    # print the number of deleted points
    length_2 = len(nodes)
    print('Deleted duplicate points:', length_1 - length_2)

    # add a specific id to each node
    nodes['ind'] = nodes.index
    nodes['id'] = 'K' + nodes['ind'].apply(str)
    nodes['type'] = 'K'

    return nodes


def insert_node_ids(lines, nodes):
    """

    :param lines:
    :param nodes:
    :return:
    """

    nodes['geo_wkt'] = nodes["geometry"].apply(lambda geom: geom.wkt)

    # add id to gdf_lines for starting and ending point
    # point as wkt
    lines['b0_wkt'] = \
        lines["geometry"].apply(lambda geom: geom.boundary[0].wkt)
    lines['b1_wkt'] = \
        lines["geometry"].apply(lambda geom: geom.boundary[-1].wkt)

    # do kind of vlookup for adding the node-ids to the lines
    # node1: starting node
    lines = lines.merge(nodes[['geo_wkt', 'id']], left_on='b0_wkt',
                        right_on='geo_wkt', suffixes=('', '_start'))

    # delete help columns
    lines.drop(axis=1, inplace=True, labels=['b0_wkt', 'geo_wkt'])

    # node1: ending node
    lines = lines.merge(nodes[['geo_wkt', 'id']], left_on='b1_wkt',
                        right_on='geo_wkt', suffixes=('', '_end'))

    # delete help columns
    lines.drop(axis=1, inplace=True, labels=['b1_wkt', 'geo_wkt'])
    nodes.drop(axis=1, inplace=True, labels=['geo_wkt'])

    a = len(lines) - lines['id_start'].count()
    b = len(lines) - lines['id_end'].count()

    print('Anzahl id_start = NaN: ', a)
    print('Anzahl id_end = NaN: ', b)

    return lines

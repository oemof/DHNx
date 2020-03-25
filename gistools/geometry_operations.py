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
import pandas as pd
from shapely.geometry import Point
from shapely import wkt
from shapely.ops import cascaded_union, nearest_points
from shapely.geometry import Point, LineString


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
    nodes['id'] = nodes.index
    nodes['id_full'] = 'forks-' + nodes['id'].apply(str)
    nodes['lat'] = nodes['geometry'].apply(lambda x: x.y)
    nodes['lon'] = nodes['geometry'].apply(lambda x: x.x)
    nodes.set_index('id', drop=True, inplace=True)

    # print the number of deleted points
    length_2 = len(nodes)
    print('Deleted duplicate points:', length_1 - length_2)

    return nodes


def insert_node_ids(lines, nodes):
    """

    :param lines:
    :param nodes:
    :return:
    """

    # add id to gdf_lines for starting and ending node
    # point as wkt
    lines['b0_wkt'] = \
        lines["geometry"].apply(lambda geom: geom.boundary[0].wkt)
    lines['b1_wkt'] = \
        lines["geometry"].apply(lambda geom: geom.boundary[-1].wkt)
    
    lines['from_node'] = lines['b0_wkt'].apply(
        lambda x: nodes.at[x, 'id_full'])
    lines['to_node'] = lines['b1_wkt'].apply(
        lambda x: nodes.at[x, 'id_full'])

    lines.drop(axis=1, inplace=True, labels=['b0_wkt', 'b1_wkt'])

    return lines


def check_double_points(gdf, radius=0.001, id_column='id'):

    """
    
    :param gdf: 
    :param radius: 
    :param id_column: 
    :return: 
    """

    l_ids = []
    count = 0

    for r, c in gdf.iterrows():

        point = c['geometry']
        gdf_other = gdf.drop([r])
        other_points = cascaded_union(gdf_other['geometry'])

        # x1 = nearest_points(point, other_points)[0]
        x2 = nearest_points(point, other_points)[1]

        if point.distance(x2) <= radius:
            l_ids.append(c[id_column])
            print('Node ', c[id_column], ' has a near neighbour!')
            print('Distanze ', point.distance(x2))
            count += 1

    print('')
    print('Number of duplicated points: ', count)

    return l_ids


def mls_to_ls(geom):

    if geom.type == 'MultiLineString':
        if len(geom) > 1:
            print('There is a REAL MultiLineString')
        geom = geom[0]

    return geom


def gdf_to_df(gdf):

    df = pd.DataFrame(
        gdf[[col for col in gdf.columns if col != gdf._geometry_column_name]])

    return df


def pair(list):

    '''Iterate over pairs in a list -> pair of points '''

    for i in range(1, len(list)):
        yield list[i - 1], list[i]


def split_linestring(linestring):
    """

    :param linestring:
    :return: a list of LineStrings
    """

    l_segments = []

    for seg_start, seg_end in pair(linestring.coords):
        line_start = Point(seg_start)
        line_end = Point(seg_end)
        segment = LineString([line_start.coords[0], line_end.coords[0]])
        # print(segment)
        l_segments.append(segment)

    return l_segments


def split_multilinestr_to_linestr(gdf_lines_streets_new):
    
    new_lines = gpd.GeoDataFrame()

    for i, b in gdf_lines_streets_new.iterrows():

        geom = b['geometry']

        if geom.type == 'MultiLineString':

            li = []
            for line in geom:
                li.append(line)  # li has always just one element?!

            # check if LineString has more than 2 points
            if len(li[0].coords) > 2:

                l_sequ = split_linestring(li[0])

                for s in l_sequ:
                    new_row = b.copy()
                    new_row['geometry'] = gpd.tools.collect(s, multi=True)
                    new_lines = new_lines.append(
                        new_row, ignore_index=True, sort=False)

                gdf_lines_streets_new.drop(index=i, inplace=True)

    gdf_lines_streets_new = gdf_lines_streets_new.append(
        new_lines, ignore_index=True, sort=False)
      
    return gdf_lines_streets_new

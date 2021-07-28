# -*- coding: utf-8 -*-

"""
This module holds functions for processing the geometry for setting up
the geometry of a ThermalNetwork based on a street geometry and a table of
buildings.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location: https://github.com/oemof/DHNx

This module is not fully tested yet, so use it with care.

SPDX-License-Identifier: MIT
"""
try:
    import geopandas as gpd

except ImportError:
    print("Need to install geopandas to process geometry data.")

try:
    from shapely.geometry import LineString
    from shapely.geometry import MultiPoint
    from shapely.geometry import Point
    from shapely.geometry import shape
    from shapely.ops import cascaded_union
    from shapely.ops import nearest_points
except ImportError:
    print("Need to install shapely to process geometry.")

import logging

import numpy as np
import pandas as pd

from . import geometry_operations as go


def line_of_point(point, gdf_lines):
    """Gets index of geometry of a GeoDataFrame, a point is located next to,
      with a distance lower than 1e-8.

    Parameters
    ----------
    point : shapely.geometry.Point
    gdf_lines : geopandas.GeoDataFrame

    Returns
    -------
    int, float or str : Index of GeoDataFrame or Warning, if no geometry found.
    """
    ind = None

    for k, l in gdf_lines.iterrows():

        if l['geometry'].distance(point) < 1e-8:
            ind = k

    if ind is None:
        return Warning('No line found which has point on it!')
    return ind


def point_to_array(point):
    """Returns the coordinates of a point as numpy.array

    Parameters
    ----------
    point : shapely.geometry.Point

    Returns
    -------
    numpy.array()
    """

    return np.array([point.x, point.y])


def calc_lot_foot(line, point):
    """
    Calculates the lot foot point.

    Parameters
    ----------
    line : shapely.geometry.LineString
    point : shapely.geometry.Point

    Returns
    -------
    shapely.geometry.Point
    """

    s_1 = shape(line).boundary[0]
    s_2 = shape(line).boundary[1]

    g_1 = point_to_array(s_1)  # end point 1 of line
    g_2 = point_to_array(s_2)  # end point 2 of line

    x_1 = point_to_array(point)

    # calculate lotfusspunkt
    u = g_2 - g_1  # vector of direction
    n = np.array([u[1], -u[0]])  # normal vector of line
    x_0 = g_1  # point on line

    y = x_1 - (np.dot((x_1 - x_0), n) / np.dot(n, n)) * n
    lot_foot_point = Point(y[0], y[1])

    # # alternative generation via intersection
    # # (=> intersections point is not exaclty on lines as well)
    # y = x_1 - 2*(np.dot((x_1 - x_0), n)/np.dot(n, n)) * n
    # lot_line = LineString([(y[0], y[1]), (x_1[0], x_1[1])])
    # lot_foot_point = lot_line.intersection(line)

    return lot_foot_point


def create_object_connections(points, lines, tol_distance=1):
    """Connects points to a line network.

    Generally, the nearest point of the next line is used as connection the point.
    Depending on the geometry, there are 3 options, the connection is created:

    - nearest point is line ending => the connection line starts from this line ending

    - nearest point is on the next line:

      a) line endings are outside the tolerance => line is split and the nearest point
      is used as connection point

      b) line endings are within the tolerance distance => the next line ending is
      used as connection point

    The tolerance distance avoids the generation of short line elements.
    This is for example the case if two buildings are directly opposite of the street.
    Using simply the nearest point method could result in very short lines.


    Parameters
    ----------
    points : geopandas.GeoDataFrame
        Points which should be connected to the line. GeoDataFrame with Points as geometry.
    lines : geopandas.GeoDataFrame
        The line-network to which the Points should be connected. The line geometry needs to
        consists of simple lines based on one starting and one ending point. LineStrings
        which contain more than 2 points are not allowed.
    tol_distance : float
        Tolerance distance for choosing the end of the line instead of the nearest point.

    Returns
    -------
    geopandas.GeoDataFrame : The newly created connection lines
    geopandas.GeoDataFrame : The updated lines (some lines are split.
        All lines should only touch at the line endings.

    """
    # check linestrings
    for _, c in lines.iterrows():
        if len(c['geometry'].coords) > 2:
            raise ValueError("The Linestrings must consists of simple lines,"
                             " with only two coordinates!")

    # empty geopandas dataframe for house connections
    conn_lines = gpd.GeoDataFrame()

    # iterate over all houses
    for index, row in points.iterrows():

        house_geo = row['geometry']

        # the same with the original lines
        all_lines = lines['geometry']
        mergedlines = cascaded_union(all_lines)

        # new nearest point method  ############ #########
        n_p = nearest_points(mergedlines, house_geo)[0]

        # get index of line which is closest to the house
        line_index = line_of_point(n_p, lines)

        # get geometry of supply line
        supply_line = lines.loc[line_index, 'geometry']

        # get end points of line
        supply_line_p0 = Point(list(supply_line.coords)[0])
        supply_line_p1 = Point(list(supply_line.coords)[1])
        supply_line_points = [supply_line_p0, supply_line_p1]
        supply_line_mulitpoints = MultiPoint(supply_line_points)

        if n_p in supply_line_points:
            # case that nearest point is a line ending

            logging.info(
                'Connect buildings... id {}: '
                'Connected to supply line ending (nearest point)'.format(index)
            )

            con_line = LineString([n_p, house_geo])

            conn_lines = conn_lines.append({'geometry': con_line}, ignore_index=True)

        else:

            dist_to_endings = [x.distance(n_p) for x in supply_line_points]

            if min(dist_to_endings) >= tol_distance:
                # line is split, no line ending is close to the nearest point
                # this also means the original supply line needs to be deleted

                logging.info(
                    'Connect buildings... id {}: Supply line split'.format(index))

                con_line = LineString([n_p, house_geo])

                conn_lines = conn_lines.append({'geometry': con_line}, ignore_index=True)

                lines.drop([line_index], inplace=True)

                lines = lines.append(
                    {'geometry': LineString([supply_line_p0, n_p])},
                    ignore_index=True
                )
                lines = lines.append(
                    {'geometry': LineString([n_p, supply_line_p1])},
                    ignore_index=True
                )

            else:
                # case that one or both line endings are closer than tolerance
                # thus, the next line ending is chosen
                logging.info(
                    'Connect buildings... id {}: Connected to Supply line ending '
                    'due to tolerance'.format(index))

                conn_point = nearest_points(supply_line_mulitpoints, n_p)[0]

                con_line = LineString([conn_point, house_geo])

                conn_lines = conn_lines.append({'geometry': con_line}, ignore_index=True)

    logging.info('Connection of buildings completed.')

    connection_lines = gpd.GeoDataFrame(conn_lines, crs=lines.crs)

    return connection_lines, lines


def check_geometry_type(gdf, types):
    """
    Checks, if a geodataframe has only the given geometry types in its GeoSeries.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        DataFrame to be checked.
    types : list
        List of types allowed for GeoDataFrame.

    """
    actual_types = set(gdf['geometry'].type)

    for type in actual_types:
        if type not in types:
            raise TypeError(
                "Your input geometry has the wrong type. "
                "Expected: {}. Got: {}".format(types, type)
            )


def create_points_from_polygons(gdf, method='midpoint'):
    """
    Converts the geometry of a polygon layer to a point layer.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
    method : str
        Method to create a point from a polygon.

    Returns
    -------
    geopandas.GeoDataFrame : GeoDataFrame with a point geometry.

    """

    if gdf['geometry'].values[0].type == 'Point':
        return gdf

    if method == 'midpoint':
        gdf['geometry'] = gdf['geometry'].centroid
        return gdf

    raise ValueError(
        'No other method than >midpoint< implemented!'
    )


def process_geometry(lines, consumers, producers,
                     method='midpoint', projected_crs=4647,
                     tol_distance=2):
    """
    This function connects the consumers and producers to the line network, and prepares the
    attributes of the geopandas.GeoDataFrames for importing as dhnx.ThermalNetwork.

    The ids of the lines are overwritten.

    Parameters
    ----------
    lines : geopandas.GeoDataFrame
        Potential routes for the DHS. Expected geometry Linestrings or MultilineStrings.
        The graph of this line network should be connected.
    consumers : geopandas.GeoDataFrame
        Location of demand/consumers. Expected geometry: Polygons or Points.
    producers : geopandas.GeoDataFrame
        Location of supply sites. Expected geometry: Polygons or Points.
    method : str
        Method for creating the point if polygons are given for the consumers and producers.
    multi_connections : bool
        Setting if a building should be connected to multiple streets.
    projected_crs : EPSG integer code
        EPSG Coordinate reference system number (eg 4647),
        which is used for the geometry operations.
        A projected crs must be used!
    tol_distance : float
        Tolerance distance at connection the points to the line network
        for choosing the end of the line instead of the lot.

    Returns
    -------
    dict : Dictionary with 4 geopandas.GeoDataFrames: The keys of the Dict are
           equal to the components of the dhnx.ThermalNetwork: 'forks', 'consumers',
           'producers', 'pipes'.

    """

    # check whether the expected geometry is used for geo dataframes
    check_geometry_type(lines, types=['LineString', 'MultiLineString'])
    for gdf in [producers, consumers]:
        check_geometry_type(gdf, types=['Polygon', 'Point', 'MultiPolygon'])

    # # split multilinestrings to single lines with only 1 starting and 1 ending point
    lines = go.split_multilinestr_to_linestr(lines)

    # check and convert crs if it is not already the `projected_crs`
    lines = go.check_crs(lines, crs=projected_crs)

    for layer in [producers, consumers]:
        layer = go.check_crs(layer, crs=projected_crs)
        layer = create_points_from_polygons(layer, method=method)
        layer.reset_index(inplace=True, drop=True)
        layer.index.name = 'id'
        if 'id' in layer.columns:
            layer.drop(['id'], axis=1, inplace=True)
        layer['lat'] = layer['geometry'].apply(lambda x: x.y)
        layer['lon'] = layer['geometry'].apply(lambda x: x.x)

    producers['id_full'] = 'producers-' + producers.index.astype('str')
    producers['type'] = 'G'
    consumers['id_full'] = 'consumers-' + consumers.index.astype('str')
    consumers['type'] = 'H'

    # Add lines to consumers and producers
    lines_consumers, lines = create_object_connections(consumers, lines, tol_distance=tol_distance)
    lines_producers, lines = create_object_connections(producers, lines, tol_distance=tol_distance)

    # Weld continuous line segments together and cut loose ends
    lines = go.weld_segments(
        lines, lines_producers, lines_consumers,
        # debug_plotting=True,
    )

    # add additional line identifier
    lines_producers['type'] = 'GL'  # GL for generation line
    lines['type'] = 'DL'  # DL for distribution line
    lines_consumers['type'] = 'HL'  # HL for house line

    # generate forks point layer
    forks = go.create_forks(lines)

    # concat lines
    lines_all = pd.concat([lines, lines_consumers, lines_producers], sort=False)
    lines_all.reset_index(inplace=True, drop=True)
    lines_all.index.name = 'id'
    if 'id' in lines_all.columns:
        lines_all.drop(['id'], axis=1, inplace=True)

    # concat point layer
    points_all = pd.concat([
        consumers[['id_full', 'geometry']],
        producers[['id_full', 'geometry']],
        forks[['id_full', 'geometry']]],
        sort=False
    )
    points_all['geo_wkt'] = points_all['geometry'].apply(lambda x: x.wkt)
    points_all.set_index('geo_wkt', drop=True, inplace=True)

    # add from_node, to_node to lines layer
    lines_all = go.insert_node_ids(lines_all, points_all)

    lines_all['length'] = lines_all.length
    logging.info(
        "Total line length is {:.0f} m".format(lines_all['length'].sum()))

    # Convert all MultiLineStrings to LineStrings
    check_geometry_type(lines_all, types=['LineString'])

    # ## check for near points
    go.check_double_points(points_all, id_column='id_full')

    return {
        'forks': forks,
        'consumers': consumers,
        'producers': producers,
        'pipes': lines_all,
    }

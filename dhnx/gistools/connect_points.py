# -*- coding: utf-8 -*-

"""
General description ... will follow.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location: https://github.com/oemof/DHNx

SPDX-License-Identifier: MIT
"""
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, shape
from shapely.ops import cascaded_union, nearest_points
import dhnx.gistools.geometry_operations as go

def line_of_point(point, gdf_lines):
    """
    :param point:
    :param gdf_lines:
    :return: Returns index of line, where point is on.
    """
    ind = 99999

    for k, l in gdf_lines.iterrows():

        if l['geometry'].distance(point) < 1e-8:
            ind = k

    if ind == 99999:
        return Warning('No line found which has point on it!')
    return ind


def point_to_array(point):
    """
    :return:
    Converts the point geometry of a geopandas information into an numpy array.
    :param point: point which should be converted into a numpy array.
    :return: numpy array
    """

    return np.array([point.x, point.y])


def calc_lot_foot(line, point):
    """
    :param line:
    :param point:
    :return: lot foot point on the line of the point
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


def cut_line_at_points(line_str, point_list):
    """
    :param line_str: line to be cut
    :param point_list: list of points the line is cut with
    :return: list of line pieces
    """
    if line_str.type == 'MultiLineString':
        line_str = line_str[0]

    # First coords of line (start + end)
    coords = [line_str.coords[0], line_str.coords[-1]]

    # Add the coords from the points
    coords += [list(p.coords)[0] for p in point_list]

    # Calculate the distance along the line for each point
    dists = [line_str.project(Point(p)) for p in coords]

    # sort the coords based on the distances
    # see http://stackoverflow.com/questions/6618515/
    # sorting-list-based-on-values-from-another-list
    coords = [p for (d, p) in sorted(zip(dists, coords))]

    # generate the Lines
    lines = [LineString([coords[i], coords[i + 1]])
             for i in range(len(coords) - 1)]

    return lines


def create_object_connections(points_objects, dist_lines):

    # empty geopandas dataframe for house connections
    conn_lines = gpd.GeoDataFrame()

    # counter for not connected houses
    count_not_connected = 0
    indices_not_connected = []
    num_houses = len(points_objects)

    # iterate over all houses
    for index, row in points_objects.iterrows():

        house_geo = row['geometry']

        # the same with the original lines
        all_lines = dist_lines['geometry']
        mergedlines = cascaded_union(all_lines)

        # new nearest point method  ############ #########
        n_p = nearest_points(mergedlines, house_geo)[0]

        # get index of line which is closest to the house
        line_index = line_of_point(n_p, dist_lines)

        # get geometry of supply line
        supply_line = dist_lines.loc[line_index, 'geometry']

        # caculate lot foot
        lot_foot = calc_lot_foot(supply_line, house_geo)

        next_line_point = nearest_points(supply_line, lot_foot)[0]

        if next_line_point.distance(lot_foot) > 1e-8:

            print('Lot außerhalb')

            con_line = LineString([next_line_point, house_geo])

            conn_lines = conn_lines.append(
                {'geometry': con_line}, ignore_index=True)

        else:   # case that the lot point is on the next supply line

            # check if end point of line is close

            # for that, check first, if multilinestring, then convert to line
            # string
            if supply_line.type == 'MultiLineString':
                l_string = supply_line[0]
            else:
                l_string = supply_line

            if len(l_string.coords) > 2:
                print("There went something wrong, Linestring with more than"
                      " 2 points!")

            supply_line_p0 = Point(list(l_string.coords)[0])
            supply_line_p1 = Point(list(l_string.coords)[1])

            # check distance from end points of lines to lot foot
            tol_distance = 2.0

            if supply_line_p0.distance(lot_foot) < tol_distance:
                print('Lotfoot closer than', tol_distance,
                      'to line end point!')
                con_line = LineString([supply_line_p0, house_geo])
                conn_lines = conn_lines.append(
                    {'geometry': con_line}, ignore_index=True)

            elif supply_line_p1.distance(lot_foot) < tol_distance:
                print('Lotfoot closer than', tol_distance,
                      'to line end point!')
                con_line = LineString([supply_line_p1, house_geo])
                conn_lines = conn_lines.append(
                    {'geometry': con_line}, ignore_index=True)

            else:
                # create lot => line to house
                lot = LineString([lot_foot, house_geo])

                # check if lot foot point is on the supply line
                if supply_line.distance(lot_foot) < 1e-8:

                    # divide supply line at lot foot point
                    split_lines = cut_line_at_points(supply_line, [lot_foot])

                    # drop original line element
                    # gdf_line_net = gdf_line_net.drop([line_index])
                    dist_lines.drop([line_index], inplace=True)

                    # add neu line elements to the geo-dataframe
                    dist_lines = dist_lines.append({'geometry': split_lines[0]},
                                                   ignore_index=True)
                    dist_lines = dist_lines.append({'geometry': split_lines[1]},
                                                   ignore_index=True)

                    # add line-to-house to geo-df
                    conn_lines = conn_lines.append(
                        {'geometry': lot}, ignore_index=True)

                else:
                    count_not_connected += 1
                    indices_not_connected.append(index)

    print(len(points_objects.index), ' of ', num_houses, 'connections calculated.')
    print('Number of not-connected objects: ', count_not_connected)
    print('Indices of not-connected objects: ', indices_not_connected)

    connection_lines = gpd.GeoDataFrame(conn_lines, crs=dist_lines.crs)

    return connection_lines, dist_lines


def check_geometry_type(gdf, types):
    """
    Checks, if a geodataframe has the only the given geometry types in its GeoSeries.

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
    else:
        if method == 'midpoint':
            gdf['geometry'] = gdf['geometry'].centroid
            return gdf
        else:
            raise ValueError(
                'No other method than >midpoint< implemented!'
            )


def process_geometry(lines=None, producers=None, consumers=None,
                     method='midpoint', multi_connections=False, projected_crs=4647):
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

    Returns
    -------
    dict : Dictionary with 4 geopandas.GeoDataFrames: The keys of the Dict are
           equal to the components of the dhnx.ThermalNetwork: 'forks', 'consumers',
           'producers', 'pipes'.

    """

    # check whether the expected geometry is used for geo dataframes
    check_geometry_type(lines, types=['LineString'])
    [check_geometry_type(gdf, types=['Polygon', 'Point']) for gdf in [producers, consumers]]

    # # split multilinestrings to single lines with only 1 starting and 1 ending point
    lines = go.split_multilinestr_to_linestr(lines)

    # check and convert crs if it is not already the `projected_crs`
    lines = go.check_crs(lines, crs=projected_crs)

    for layer in [producers, consumers]:
        layer = go.check_crs(layer, crs=projected_crs)
        layer = create_points_from_polygons(layer, method=method)
        layer.reset_index(inplace=True, drop=True)
        layer.index.name = 'id'
        layer['lat'] = layer['geometry'].apply(lambda x: x.y)
        layer['lon'] = layer['geometry'].apply(lambda x: x.x)

    producers['id_full'] = 'producers-' + producers.index.astype('str')
    producers['type'] = 'G'
    consumers['id_full'] = 'consumers-' + consumers.index.astype('str')
    consumers['type'] = 'H'

    # Add lines to consumers and producers
    lines_consumers, lines = create_object_connections(consumers, lines)
    lines_producers, lines = create_object_connections(producers, lines)

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
    forks = go.create_nodes(lines)

    # concat lines
    lines_all = pd.concat([lines, lines_consumers, lines_producers], sort=False)
    lines_all.reset_index(inplace=True, drop=True)
    lines_all.index.name = 'id'

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
    print("Total line length is {:.0f} m".format(lines_all['length'].sum()))

    # Convert all MultiLineStrings to LineStrings
    lines_all['geometry'] = lines_all['geometry'].apply(lambda x: go.mls_to_ls(x))

    # ## check for near points
    go.check_double_points(points_all, id_column='id_full')

    return {
        'forks': forks,
        'consumers': consumers,
        'producers': producers,
        'pipes': lines_all,
    }

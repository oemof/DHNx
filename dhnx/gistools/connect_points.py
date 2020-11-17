# -*- coding: utf-8 -*-

"""
General description ... will follow.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location: https://github.com/oemof/DHNx

SPDX-License-Identifier: MIT
"""
import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, shape
from shapely.ops import cascaded_union, nearest_points
from shapely import affinity
from dhnx.gistools import geometry_operations as go


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
    else:
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


def create_object_connections_2(points_objects, dist_lines):

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
        np = nearest_points(mergedlines, house_geo)[0]

        # get index of line which is closest to the house
        line_index = line_of_point(np, dist_lines)

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

    return conn_lines, dist_lines

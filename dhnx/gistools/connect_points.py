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
    from shapely.ops import nearest_points
    from shapely.ops import unary_union
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
    s_1 = Point(line.coords[0])
    s_2 = Point(line.coords[-1])

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

    # Pepare merging all the street lines
    all_lines = lines['geometry']

    # There seems to be a conflict between shapely and pygeos,
    # which both use 'geos' internally, if both are installed.
    # This can cause
    # 'OSError exception: access violation reading 0xFFFFFFFFFFFFFFFF'.
    #
    # With shapely 1.8.0 and pygeos 0.12.0 it was observed that
    # this sometimes even fails without error. In such a case
    # mergedlines might only contain a single LineString (one street
    # segment) instead of a MultiLineString (the combined network
    # of all street segments). This completely messes up the
    # following nearest_points().
    #
    # Wrapping the argument in 'list()' seems to be a valid workaround.
    # It may come with a performance cost, as noted here:
    # https://github.com/geopandas/geopandas/issues/1820
    # https://github.com/geopandas/geopandas/issues/2171
    # This issue may disappear when shapely 2.0 is released (then pygeos
    # is merged with shapely).
    mergedlines = unary_union(list(all_lines))
    # mergedlines = unary_union(all_lines)  # TODO Try this with shapely 2.0

    # empty geopandas dataframe for house connections
    conn_lines = gpd.GeoDataFrame(geometry=[], crs=lines.crs)

    # iterate over all houses
    for index, row in points.iterrows():

        house_geo = row['geometry']

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

            logging.debug(
                'Connect buildings... id {}: '
                'Connected to supply line ending (nearest point)'.format(index)
            )

            con_line = LineString([n_p, house_geo])

            conn_lines = pd.concat(
                [gpd.GeoDataFrame(conn_lines, crs=lines.crs),
                 gpd.GeoDataFrame(geometry=[con_line], crs=lines.crs)],
                ignore_index=True)

        else:

            dist_to_endings = [x.distance(n_p) for x in supply_line_points]

            if min(dist_to_endings) >= tol_distance:
                # line is split, no line ending is close to the nearest point
                # this also means the original supply line needs to be deleted

                logging.debug(
                    'Connect buildings... id {}: Supply line split'.format(index))

                con_line = LineString([n_p, house_geo])

                conn_lines = pd.concat(
                    [gpd.GeoDataFrame(conn_lines, crs=lines.crs),
                     gpd.GeoDataFrame(geometry=[con_line], crs=lines.crs)],
                    ignore_index=True)

                lines.drop([line_index], inplace=True)

                lines = pd.concat(
                    [gpd.GeoDataFrame(lines, crs=lines.crs),
                     gpd.GeoDataFrame(geometry=[
                         LineString([supply_line_p0, n_p]),
                         LineString([n_p, supply_line_p1])], crs=lines.crs)],
                    ignore_index=True)

            else:
                # case that one or both line endings are closer than tolerance
                # thus, the next line ending is chosen
                logging.debug(
                    'Connect buildings... id {}: Connected to Supply line '
                    'ending due to tolerance'.format(index))

                conn_point = nearest_points(supply_line_mulitpoints, n_p)[0]

                con_line = LineString([conn_point, house_geo])

                conn_lines = pd.concat(
                    [gpd.GeoDataFrame(conn_lines, crs=lines.crs),
                     gpd.GeoDataFrame(geometry=[con_line], crs=lines.crs)],
                    ignore_index=True)

    logging.info('Connection of buildings completed.')

    return conn_lines, lines


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

    if gdf['geometry'].values[0].geom_type == 'Point':
        return gdf

    if method == 'midpoint' or method == 'boundary':
        # (method 'boundary' is performed later and needs the centroid)
        gdf['geometry'] = gdf['geometry'].centroid
        return gdf

    raise ValueError(
        "No other methods than 'midpoint' and 'boundary' implemented!"
    )


def run_point_method_boundary(
        consumers_poly, consumers, producers_poly, producers,
        lines_consumers, lines_producers):
    """Run 'boundary' method for finding the building connection point.

    The 'midpoint' method (using the centroid) must already have been run,
    generating the default connection lines from street to centroid.

    If there is only one intersection between that line and the boundary
    of the building, this intersection point is used as the connection
    point instead (and the connection line is shortened accordingly).

    However, complex building shapes can produce multiple intersections. In
    this case, the intersection with the 'convex hull' of the building is used
    instead. This may result in connection points that do not touch an
    actual building wall, but it should still be an improvement compared to
    the 'midpoint' method.

    In case of no intersections with the building boundary (possible for e.g.
    U-shaped buildings), the original centroid is used.

    Parameters
    ----------
    consumers_poly : geopandas.GeoDataFrame
        Polygons of the consumer buildings. Point geometries are also allowed,
        but they are not changed.
    consumers : geopandas.GeoDataFrame
        Points of the consumer buildings (as returned by 'midpoint' method).
    producers_poly : geopandas.GeoDataFrame
        Polygons of the producer buildings. Point geometries are also allowed,
        but they are not changed.
    producers : geopandas.GeoDataFrame
        Points of the producer buildings (as returned by 'midpoint' method).
    lines_consumers : geopandas.GeoDataFrame
        Connection lines from street to each consumer point.
    lines_producers : geopandas.GeoDataFrame
        Connection lines from street to each producer point.

    Returns
    -------
    consumers : geopandas.GeoDataFrame
        Updated points of the consumer buildings.
    producers : geopandas.GeoDataFrame
        Updated points of the producer buildings.
    lines_consumers : geopandas.GeoDataFrame
        Updated connection lines from street to each consumer point.
    lines_producers : geopandas.GeoDataFrame
        Updated connection lines from street to each producer point.

    """
    logging.info('Run "boundary" method for finding the building connections')
    # Cut the part off of each "line_consumer" that is within the building
    # polygon. As a result, the heating grid will only reach to the wall of
    # the building.
    lines_consumers_n = gpd.GeoDataFrame(
        geometry=lines_consumers.difference(consumers_poly, align=False))
    # This produces a MultiLineString for complex building polygons, where
    # the boundary and the simple lines from centroid to street intersect
    # multiple times. This would not be a valid connection line. In those
    # cases the 'convex hull' of the building is used instead.
    lines_consumers_n.loc[lines_consumers_n.type == "MultiLineString"] = \
        gpd.GeoDataFrame(geometry=lines_consumers.difference(
            consumers_poly.convex_hull, align=False))

    # Repeat for the producer lines
    lines_producers_n = gpd.GeoDataFrame(geometry=lines_producers.difference(
        producers_poly, align=False))
    lines_producers_n.loc[lines_producers_n.type == "MultiLineString"] = \
        gpd.GeoDataFrame(geometry=lines_producers.difference(
            producers_poly.convex_hull, align=False))

    # Now the "consumers" (point objects for each building) need to be
    # updated to touch the end of the consumer_lines
    consumers_n = gpd.GeoDataFrame(geometry=lines_consumers.intersection(
        consumers_poly.boundary, align=False))
    consumers_n.loc[consumers_n.type == "MultiPoint"] = \
        gpd.GeoDataFrame(geometry=lines_consumers.intersection(
            consumers_poly.convex_hull.boundary, align=False))

    # Repeat for the producers
    producers_n = gpd.GeoDataFrame(geometry=lines_producers.intersection(
        producers_poly.convex_hull.boundary, align=False))
    producers_n.loc[producers_n.type == "MultiPoint"] = \
        gpd.GeoDataFrame(geometry=lines_producers.intersection(
            producers_poly.convex_hull.boundary, align=False))

    # Sometimes the centroid does not lie within a building and there may be
    # no intersetions, i.e. the new point is an 'empty' geometry. This can
    # happen if buildings are multipolygons, which is not forbidden.
    # Sometimes the new lines are empty (e.g. because a street and a building
    # object cross each other).
    # In these cases the original geometry is used for points and lines.
    mask = (consumers_n.is_empty | lines_consumers_n.is_empty)
    consumers_n.loc[mask] = consumers.loc[mask].geometry
    lines_consumers_n.loc[mask] = lines_consumers.loc[mask].geometry

    mask = (producers_n.is_empty | lines_producers_n.is_empty)
    producers_n.loc[mask] = producers.loc[mask].geometry
    lines_producers_n.loc[mask] = lines_producers.loc[mask].geometry

    # Now update all the original variables with the new data
    consumers.geometry = consumers_n.geometry
    producers.geometry = producers_n.geometry
    lines_consumers = lines_consumers_n
    lines_producers = lines_producers_n

    return consumers, producers, lines_consumers, lines_producers


def check_duplicate_geometries(gdf):
    """Test the input GeoDataFrame for duplicate geometries and plot them."""
    if gdf.duplicated(subset="geometry").any():
        idx = gdf.duplicated(subset="geometry")
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(dpi=200)
            gdf.loc[~idx].plot(ax=ax, color='green')
            gdf.loc[idx].plot(ax=ax, color='red')
            plt.title("Red are duplicate geometries. Please fix!")
            plt.show()
        except ImportError:
            logging.info("Install matplotlib to show a plot of the duplicate "
                         "geometries.")
        raise ValueError("GeoDataFrame has {} duplicate geometries"
                         .format(len(gdf.loc[idx])))


def process_geometry(lines, consumers, producers,
                     method='midpoint', projected_crs=4647,
                     tol_distance=2, reset_index=True):
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
        Method for creating the point if polygons are given for the consumers
        and producers. Method 'midpoint' uses the centroid of each building
        polygon. Method 'boundary' moves the point to the boundary (wall) of
        the building, along the line constructed from centroid to the street.
    multi_connections : bool
        Setting if a building should be connected to multiple streets.
    projected_crs : EPSG integer code
        EPSG Coordinate reference system number (eg 4647),
        which is used for the geometry operations.
        A projected crs must be used!
    tol_distance : float
        Tolerance distance at connection the points to the line network
        for choosing the end of the line instead of the lot.
    reset_index : bool
        If True, reset the index and ignore the existing index. If False,
        use the existing index for consumer and producer identificators.
        Default: True

    Returns
    -------
    dict : Dictionary with 4 geopandas.GeoDataFrames: The keys of the Dict are
           equal to the components of the dhnx.ThermalNetwork: 'forks', 'consumers',
           'producers', 'pipes'.

    """
    if method == 'boundary':
        # copies of the original polygons are needed for method 'boundary'
        consumers_poly = go.check_crs(consumers, crs=projected_crs).copy()
        producers_poly = go.check_crs(producers, crs=projected_crs).copy()

    # check whether the expected geometry is used for geo dataframes
    check_geometry_type(lines, types=['LineString', 'MultiLineString'])
    for gdf in [producers, consumers]:
        check_geometry_type(gdf, types=['Polygon', 'Point', 'MultiPolygon'])
        check_duplicate_geometries(gdf)

    # split multilinestrings to single lines with only 1 starting and 1 ending point
    lines = go.split_multilinestr_to_linestr(lines)

    # check and convert crs if it is not already the `projected_crs`
    lines = go.check_crs(lines, crs=projected_crs)

    for layer in [producers, consumers]:
        layer = go.check_crs(layer, crs=projected_crs)
        layer = create_points_from_polygons(layer, method=method)
        if reset_index:
            layer.reset_index(inplace=True, drop=True)
            layer.index.name = 'id'
            if 'id' in layer.columns:
                layer.drop(['id'], axis=1, inplace=True)
        else:
            if layer.index.has_duplicates:
                raise ValueError("The index of input data has duplicate "
                                 "values, which is not allowed")
        layer['lat'] = layer['geometry'].apply(lambda x: x.y)
        layer['lon'] = layer['geometry'].apply(lambda x: x.x)

    producers['id_full'] = 'producers-' + producers.index.astype('str')
    producers['type'] = 'G'
    consumers['id_full'] = 'consumers-' + consumers.index.astype('str')
    consumers['type'] = 'H'

    # Add lines to consumers and producers
    lines_consumers, lines = create_object_connections(
        consumers, lines, tol_distance=tol_distance)
    lines_producers, lines = create_object_connections(
        producers, lines, tol_distance=tol_distance)
    if not reset_index:
        # Connection lines are ordered the same as points. Match their indexes
        lines_consumers.index = consumers.index
        lines_producers.index = producers.index

    if method == 'boundary':
        # Can only be performed after 'midpoint' method
        consumers, producers, lines_consumers, lines_producers = (
            run_point_method_boundary(
                consumers_poly, consumers, producers_poly, producers,
                lines_consumers, lines_producers))

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
    if reset_index:
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

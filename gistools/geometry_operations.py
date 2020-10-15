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
import shapely
from shapely import wkt
from shapely.ops import cascaded_union, nearest_points
from shapely.geometry import Point, LineString
import matplotlib.pyplot as plt


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

    nodes = gpd.GeoDataFrame(geometry=[], crs=lines.crs)

    for i, r in lines.iterrows():
        geom = lines.iloc[i]['geometry']
        p_0 = Point(geom.boundary[0])
        p_1 = Point(geom.boundary[-1])
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

    lines['from_node'] = lines['b0_wkt'].apply(lambda x: nodes.at[x,
                                                                  'id_full'])
    lines['to_node'] = lines['b1_wkt'].apply(lambda x: nodes.at[x, 'id_full'])

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
            print('Node ', c[id_column], ' has a near neighbour!',
                  'Distance ', point.distance(x2))
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

        elif len(geom.coords) > 2:

            num_new_lines = len(geom.coords) - 1

            for num in range(num_new_lines):
                new_row = b.copy()
                new_row['geometry'] = \
                    LineString([geom.coords[num], geom.coords[num + 1]])
                new_lines = new_lines.append(
                    new_row, ignore_index=True, sort=False)

            gdf_lines_streets_new.drop(index=i, inplace=True)

    gdf_lines_streets_new = gdf_lines_streets_new.append(
        new_lines, ignore_index=True, sort=False)

    return gdf_lines_streets_new


def cut_loose_ends(gdf_line_net, gdf_line_gen, gdf_line_houses):
    """Recursively cut loose ends.

    This functionality is also included in ``weld_segments()``.
    """
    gdf_line_net_last = gdf_line_net
    gdf_line_net_new = _cut_loose_ends(gdf_line_net, gdf_line_gen,
                                       gdf_line_houses)
    # Now do this recursively, until the problem cannot be simplified further
    while len(gdf_line_net_new) < len(gdf_line_net_last):
        print('Cutting loose ends... reduced from {} to {} lines'.format(
            len(gdf_line_net_last), len(gdf_line_net_new)))
        gdf_line_net_last = gdf_line_net_new
        gdf_line_net_new = _cut_loose_ends(gdf_line_net_new, gdf_line_gen,
                                           gdf_line_houses)
    return gdf_line_net_new


def _cut_loose_ends(gdf_line_net, gdf_line_gen, gdf_line_houses):
    """Cut loose ends by keeping only what connects to other lines.

    This functionality is also included in ``weld_segments()``.
    """
    gdf_line_net_new = gpd.GeoDataFrame(geometry=[])
    for i, b in gdf_line_net.iterrows():
        geom = b.geometry

        # Keep lines that are connected to generator or house
        mask_gen = [geom.touches(g) for g in gdf_line_gen.geometry]
        mask_houses = [geom.touches(g) for g in gdf_line_houses.geometry]
        if any(mask_gen) or any(mask_houses):
            gdf_line_net_new = gdf_line_net_new.append(b, ignore_index=True)
            continue

        # Find the neighbours of the current line segment
        mask_neighbours = [geom.touches(g) for g in gdf_line_net.geometry]
        neighbours = gdf_line_net[mask_neighbours]

        # If all of the neighbours intersect with each other, it is the
        # last segement before an intersection, which can be removed
        for neighbour in neighbours.geometry:
            if all([neighbour.intersects(g) for g in neighbours.geometry]):
                neighbours = gpd.GeoDataFrame(geometry=[])

        if len(neighbours) <= 1:
            continue  # This is an unused end segment, which we can discard
        else:  # Keep anything with more than one neighbour
            gdf_line_net_new = gdf_line_net_new.append(b, ignore_index=True)

    return gdf_line_net_new


def weld_segments(gdf_line_net, gdf_line_gen, gdf_line_houses,
                  debug_plotting=False):
    """Weld continuous line segments together and cut loose ends.

    This is a public function that recursively calls the internal function
    weld_line_segments_(), until the problem cannot be simplified futher.

    Find all lines that only connect to one other line and connect those
    to a single MultiLine object. Points that connect to Generators and
    Houses are not simplified. Loose ends are shortened where possible.

    Args:
        gdf_line_net (GeoDataFrame): Potential pipe network.

        gdf_line_gen (GeoDataFrame): Generators that need to be connected.

        gdf_line_houses (GeoDataFrame): Houses that need to be connected.

        debug_plotting (bool, optional): Plot the selection process.

    Returns:
        gdf_line_net_new (GeoDataFrame): Simplified potential pipe network.

    """
    gdf_line_net_last = gdf_line_net
    gdf_line_net_new = _weld_segments(gdf_line_net, gdf_line_gen,
                                      gdf_line_houses, debug_plotting)
    # Now do all of this recursively
    while len(gdf_line_net_new) < len(gdf_line_net_last):
        print('Welding lines... reduced from {} to {} lines'.format(
            len(gdf_line_net_last), len(gdf_line_net_new)))
        gdf_line_net_last = gdf_line_net_new
        gdf_line_net_new = _weld_segments(gdf_line_net_new, gdf_line_gen,
                                          gdf_line_houses, debug_plotting)
    return gdf_line_net_new


def _weld_segments(gdf_line_net, gdf_line_gen, gdf_line_houses,
                   debug_plotting=False):
    """Weld continuous line segments together and cut loose ends.

    Find all lines that only connect to one other line and connect those
    to a single MultiLine object. Points that connect to Generators and
    Houses are not simplified. Loose ends are shortened where possible.

    Args:
        gdf_line_net (GeoDataFrame): Potential pipe network.

        gdf_line_gen (GeoDataFrame): Generators that need to be connected.

        gdf_line_houses (GeoDataFrame): Houses that need to be connected.

        debug_plotting (bool, optional): Plot the selection process.

    Returns:
        gdf_line_net_new (GeoDataFrame): Simplified potential pipe network.

    """
    gdf_line_net_new = gpd.GeoDataFrame(geometry=[])
    gdf_merged_all = gpd.GeoDataFrame(geometry=[])
    gdf_deleted = gpd.GeoDataFrame(geometry=[])

    for i, b in gdf_line_net.iterrows():
        def debug_plot(neighbours, color='red'):
            """Plot base map, current segment (with color) and neighbours."""
            if debug_plotting:
                fig, ax = plt.subplots(1, 1, dpi=300)
                gdf_line_net.plot(ax=ax, color='blue')
                gdf_line_gen.plot(ax=ax, color='green')
                gdf_line_houses.plot(ax=ax, color='green')
                if len(neighbours) > 0:  # Prevent empty plot warning
                    neighbours.plot(ax=ax, color='orange')
                gpd.GeoDataFrame(geometry=[geom]).plot(ax=ax, color=color)

        geom = b.geometry  # The current line segment

        if any([geom.within(g) for g in gdf_merged_all.geometry]):
            # Drop this object, because it is contained within a merged object
            continue  # Continue with the next line segment

        # Find out if current segment connects to a generator or a house
        mask_gen = [geom.touches(g) for g in gdf_line_gen.geometry]
        mask_houses = [geom.touches(g) for g in gdf_line_houses.geometry]
        mask_new = [geom.overlaps(g) for g in gdf_line_net_new.geometry]

        if any(mask_gen) or any(mask_houses) or any(mask_new):
            # Keep this segment unchanged, because it is connected to a
            # generator, a house or "new" geometry (which is kept)
            gdf_line_net_new = gdf_line_net_new.append(b, ignore_index=True)
            continue  # Continue with the next line segment

        # Find all neighbours of the current segment
        mask_neighbours = [geom.touches(g) for g in gdf_line_net.geometry]
        neighbours = gdf_line_net[mask_neighbours]
        # If all of the neighbours intersect with each other, it is the
        # last segement before an intersection, which can be removed
        for neighbour in neighbours.geometry:
            if all([neighbour.intersects(g) for g in neighbours.geometry]):
                neighbours = gpd.GeoDataFrame(geometry=[])

        if len(neighbours) <= 1:
            # Skip: This is an unused end segment, which we can discard to
            # simplify the network
            debug_plot(neighbours, color='white')
            gdf_deleted = gdf_deleted.append(b, ignore_index=True)
            continue  # Continue with the next line segment

        elif len(neighbours) > 2:
            # This segment has more than two neighbours. This means it is
            # part of an intersection, which we do not simplify futher.
            # However, we can check if either endpoint of the current segment
            # only has one neighbour. Then that one can still be merged.
            p1 = geom.boundary[0]
            p2 = geom.boundary[-1]
            p1_neighbours = [p1.intersects(g) for g in neighbours.geometry]
            p2_neighbours = [p2.intersects(g) for g in neighbours.geometry]
            if p1_neighbours.count(True) == 1:  # Only one neighbour allowed
                neighbours = neighbours[p1_neighbours]  # Neighbour to merge
            elif p2_neighbours.count(True) == 1:  # Only one neighbour allowed
                neighbours = neighbours[p2_neighbours]  # Neighbour to merge
            else:  # Keep this segment. Multiple lines meet at an intersection
                gdf_line_net_new = gdf_line_net_new.append(b,
                                                           ignore_index=True)
                debug_plot(neighbours, color='green')
                continue  # Continue with the next line segment

        elif len(neighbours) == 2:
            # There are excactly two separate neighbours that can be merged
            pass  # Run the rest of the loop

        # Before merging, we need to futher clean up the list of neighbours
        neighbours_list = []
        for neighbour in neighbours.geometry:
            if any([neighbour.equals(g) for g in gdf_deleted.geometry]):
                continue  # Do not use neighbour that has already been deleted
            elif any([neighbour.within(g) for g in gdf_line_net_new.geometry]):
                continue  # Prevent creating dublicates
            elif any([neighbour.touches(g) for g in neighbours.geometry]):
                neighbours_list = []  # The two neighbours touch
                break  # This is a intersection that cannot be simplified
            else:  # Choose neighbour for merging
                neighbours_list.append(neighbour)
        neighbours = gpd.GeoDataFrame(geometry=neighbours_list)

        # Create list of all elements that should be merged
        lines = [geom] + list(neighbours.geometry)
        try:  # Works when all elements are LineStrings
            # Combine lines into a multi-linestring
            multi_line = shapely.geometry.MultiLineString(lines)
        except NotImplementedError:  # Fails if there is a MultiLineString
            lines_ = []  # Create a new list of lines, without MultiLineStrings
            for line in lines:
                if line.type == 'MultiLineString':
                    lines_ += list(line)  # Split the MultiLineString
                else:  # Linestring
                    lines_.append(line)
            # Now combine all of those into MultiLineString
            multi_line = shapely.geometry.MultiLineString(lines_)

        # Merge the MultiLineString into a single object
        merged_line = shapely.ops.linemerge(multi_line)
        gdf_merged = gpd.GeoDataFrame(geometry=[merged_line])
        debug_plot(neighbours)  # Plot the segments before the merge
        debug_plot(gdf_merged, color='orange')  # ...and after the merge
        gdf_line_net_new = gdf_line_net_new.append(gdf_merged,
                                                   ignore_index=True)
        gdf_merged_all = gdf_merged_all.append(gdf_merged, ignore_index=True)

    return gdf_line_net_new

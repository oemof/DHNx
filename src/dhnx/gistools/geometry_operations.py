# -*- coding: utf-8 -*-

"""
This modules holds functions for geometry operations, that are needed for
the geometry processing module `connect_points.py`.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location: https://github.com/oemof/DHNx

This module is not fully tested yet, so use it with care.

SPDX-License-Identifier: MIT
"""

import math

try:
    import geopandas as gpd
except ImportError:
    print("Need to install geopandas to process geometry data.")

import networkx as nx

try:
    import shapely
    from shapely import wkt
    from shapely.geometry import LineString
    from shapely.geometry import Point
    from shapely.geometry import mapping
    from shapely.ops import nearest_points
    from shapely.ops import unary_union
except ImportError:
    print("Need to install shapely to process geometry.")

import logging

import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)  # Create a logger for this module


def create_forks(lines):
    """
    Creates a forks(nodes) GeoDataFrame from a "line"-GeoDataFrame
    based on the end-points of each LineString.

    Also, an index for every fork is given, and the columns 'full-id'
    (="forks-" + index"), 'lat' and 'lon', which results from the geometry,
    are added to the GeoDataFrame.

    Parameters
    ----------
    lines : geopandas.GeoDataFrame

    Returns
    -------
    geopandas.GeoDataFrame : GeoDataFrame with Points as geometry.

    """
    nodes = gpd.GeoDataFrame(geometry=[], crs=lines.crs)

    for _, j in lines.iterrows():
        geom = j["geometry"]
        p_0 = Point(geom.boundary.geoms[0])
        p_1 = Point(geom.boundary.geoms[-1])
        nodes = pd.concat(
            [nodes, gpd.GeoDataFrame(geometry=[p_0, p_1], crs=lines.crs)],
            ignore_index=True,
        )

    # transform geometry into wkt
    nodes["geometry_wkt"] = nodes["geometry"].apply(lambda geom: geom.wkt)

    # drop duplicates of geometry column
    nodes = nodes.drop_duplicates(["geometry_wkt"])

    # create shapely geometry again
    nodes["geometry"] = nodes["geometry_wkt"].apply(
        lambda geom: wkt.loads(geom)
    )  # pylint: disable=unnecessary-lambda

    # set index for forks
    nodes = nodes.reset_index(drop=True)
    nodes["id"] = nodes.index
    nodes["id_full"] = "forks-" + nodes["id"].apply(str)
    nodes["lat"] = nodes["geometry"].apply(lambda x: x.y)
    nodes["lon"] = nodes["geometry"].apply(lambda x: x.x)
    nodes.set_index("id", drop=True, inplace=True)

    return nodes


def insert_node_ids(lines, nodes):
    """Create the columns `from_node`, `to_node` and insert the node ids.

    The node ids are called e.g. forks-3, consumers-5 etc.
    The updated "line"-GeoDataFrame is returned.

    Parameters
    ----------
    lines : geopandas.GeoDataFrame
    nodes : geopandas.GeoDataFrame

    Returns
    -------
    geopandas.GeoDataFrame
    """
    nodes["geo_wkt"] = nodes.geometry.apply(
        lambda x: wkt.dumps(x, output_dimension=2)
    )
    nodes.set_index("geo_wkt", drop=True, inplace=True)

    # add id to gdf_lines for starting and ending node point as wkt
    lines["b0_wkt"] = lines.geometry.apply(
        lambda geom: wkt.dumps(geom.boundary.geoms[0], output_dimension=2)
    )
    lines["b1_wkt"] = lines.geometry.apply(
        lambda geom: wkt.dumps(geom.boundary.geoms[-1], output_dimension=2)
    )

    def match_multipoint(point_wkt):
        """Return id_full from matching 'nodes' for each point in point_wkt.

        This is necessary if point_wkt contains MultiPoint objects, which
        result from multiple connection lines, and not only single Point
        objects.
        """
        point_line = wkt.loads(point_wkt)
        for point_node in nodes.index:
            if point_line.within(wkt.loads(point_node)):
                return nodes.loc[point_node, "id_full"]
        logger.error("Point not found: %s", point_wkt)
        return False

    try:
        lines["from_node"] = lines["b0_wkt"].apply(
            lambda x: nodes.at[x, "id_full"]
        )
        lines["to_node"] = lines["b1_wkt"].apply(lambda x: match_multipoint(x))
    except KeyError as e:
        errors = [
            wkt.loads(x) for x in lines["b0_wkt"] if x not in nodes["id_full"]
        ]
        errors.extend(
            [wkt.loads(x) for x in lines["b1_wkt"] if not match_multipoint(x)]
        )
        gdf_errors = gpd.GeoDataFrame(geometry=errors, crs=lines.crs)
        ax = lines.plot()
        gdf_errors.plot(ax=ax, color="red", label="Point(s) causing error")
        plt.legend()
        plt.show()
        try:
            nodes.to_file("debug_nodes.geojson")
            gdf_errors.to_file("debug_error_points.geojson")
            # lines[[lines.geometry.name, 'type', 'b0_wkt', 'b1_wkt']
            #       ].to_file('debug_lines.geojson')
        except Exception as e:
            breakpoint()
            logger.error(e)

        raise KeyError(
            "This error indicates specific problems with the data. "
            "A plot of the problematic point(s) is shown."
        ) from e

    lines.drop(axis=1, inplace=True, labels=["b0_wkt", "b1_wkt"])

    return lines


def check_double_points(gdf, radius=0.001, id_column=None):
    """Check for points, which are close to each other.

    In case, two points are close, the index of the points are printed.

    Parameters
    ----------
    gdf : geopandas.GeoDataFrame
        GeoDataFrame with Points as geometry.
    radius : float
        Maximum distance.
    id_column : str or None
        Column name which should be printed in case of near points.
        If None, the index is printed.

    Returns
    -------
    list : Indices of "near" points.
    """

    l_ids = []
    count = 0

    for r, c in gdf.iterrows():

        point = c["geometry"]
        gdf_other = gdf.drop([r])
        # Prevent OSError, see https://github.com/oemof/DHNx/issues/107
        other_points = unary_union(list(gdf_other["geometry"]))

        # x1 = nearest_points(point, other_points)[0]
        x2 = nearest_points(point, other_points)[1]

        if point.distance(x2) <= radius:
            l_ids.append(r)

            if id_column is None:
                print_name = r
            else:
                print_name = c[id_column]

            logger.info(
                "Node {} has a near neighbour! "
                "Distance {}".format(print_name, point.distance(x2))
            )

            count += 1

    if count > 0:
        logger.info("Number of duplicated points: %s", count)
    else:
        logger.info(
            "Check passed: No points with a distance closer than {}".format(
                radius
            )
        )

    return l_ids


def gdf_to_df(df):
    """Converts a GeoDataFrame to a pandas.DataFrame by deleting the geometry
    column."""
    if isinstance(df, gpd.GeoDataFrame):
        df = df.drop(columns=df.geometry.name)

    return df


def split_multilinestr_to_linestr(gdf_input):
    """Simplifies GeoDataFrames with LineStrings as geometry.

    The LineStrings (whether LineStrings, or MulitLineStings) are split into
    LineStrings with only two coordinates, one starting and one ending point.

    The other values of the GeoDataFrame are copied to the new rows
    for each row, who's geometry is split.

    Parameters
    ----------
    gdf_lines : geopandas.GeoDataFrame

    Returns
    -------
    geopandas.GeoDataFrame
    """
    gdf_lines = gdf_input.copy()

    new_lines = gpd.GeoDataFrame()

    # first: split MultiLineString into LineStrings
    for i, b in gdf_lines.iterrows():

        geom = b["geometry"]

        if geom.geom_type == "MultiLineString":

            multilinestrings = []

            for line in mapping(geom)["coordinates"]:
                multilinestrings.append(LineString(line))

            for multiline in multilinestrings:
                new_row = b.copy()
                new_row["geometry"] = multiline
                new_lines = pd.concat(
                    [new_lines, new_row.to_frame().T],
                    ignore_index=True,
                    sort=False,
                )

            gdf_lines.drop(index=i, inplace=True)

    gdf_lines = pd.concat(
        [gdf_lines, new_lines], ignore_index=True, sort=False
    )

    gdf_lines["geometry"].crs = gdf_input.crs

    # second: split LineStrings into single Linestrings
    new_lines = gpd.GeoDataFrame()
    for i, b in gdf_lines.iterrows():

        geom = b["geometry"]

        if len(geom.coords) > 2:

            num_new_lines = len(geom.coords) - 1

            for num in range(num_new_lines):
                new_row = b.copy()
                new_row["geometry"] = LineString(
                    [geom.coords[num], geom.coords[num + 1]]
                )
                new_lines = pd.concat(
                    [new_lines, new_row.to_frame().T],
                    ignore_index=True,
                    sort=False,
                )

            gdf_lines.drop(index=i, inplace=True)

    gdf_lines = pd.concat(
        [gdf_lines, new_lines], ignore_index=True, sort=False
    )

    gdf_lines["geometry"].crs = gdf_input.crs

    return gdf_lines


def drop_parallel_lines(gdf):
    """Keep only the shortest of all lines connecting the same two points.

    This prevents an error in eomof.solph that will occur if multiple lines
    connect the same two points in a network.

    These can be two actually distinct paths between two points, or two
    identical lines on top of each other. When downloading streets with osmnx,
    this can introduce such duplicates where the two have the attributes
    'reversed=True' and 'reversed=False'

    This function modifies the GeoDataFrame in place and resets the index.
    """
    # Stores each LineString's endpoints and length in temporary columns
    gdf["5d7u6j_endpoints"] = gdf.geometry.apply(
        lambda line: tuple(sorted([line.coords[0], line.coords[-1]]))
    )
    gdf["5d7u6j_length"] = gdf.geometry.length

    # Group by endpoints and keep only the shortest LineString for each group
    gdf = (
        gdf.sort_values("5d7u6j_length")
        .groupby("5d7u6j_endpoints")
        .first()
        .set_crs(gdf.crs)  # The groupby operation removes crs info
        .reset_index(drop=True)  # Drop the temporary columns
        .drop(columns=["5d7u6j_length"])  # Drop the temporary columns
    )
    return gdf


def _line_string(
    path_edges: list,
    lines_all: gpd.GeoDataFrame,
) -> LineString:
    """
    Create a LineString from a list of 2-tuples of node names,
    combined from LineStrings found in lines_all.
    """
    ordered = []
    last_segment = None
    for segment in path_edges:
        orientation = 1
        if last_segment:
            if segment[0] not in last_segment:
                # current segment pointing away from last one
                orientation = -1
        elif len(path_edges) >= 2 and segment[1] not in path_edges[1]:
            # first segment pointing away from second one
            orientation = -1

        path_edge_geometry = lines_all[
            (lines_all["from_node"] == segment[0])
            & (lines_all["to_node"] == segment[1])
        ]["geometry"]

        if path_edge_geometry.empty:
            # also in lines_all, the segment points away from last one
            orientation *= -1
            path_edge_geometry = lines_all[
                (lines_all["from_node"] == segment[1])
                & (lines_all["to_node"] == segment[0])
            ]["geometry"]

        # As slicing and inverting in one step needs extra caution,
        # we invert here, if applicable.
        path_edge_geometry = list(path_edge_geometry.iloc[0].coords)[
            ::orientation
        ]

        # Append while avoiding duplicate junction point
        if not ordered:
            ordered.extend(path_edge_geometry)
        else:
            ordered.extend(path_edge_geometry[1:])

        last_segment = segment

    return LineString(ordered)


def simplify(
    lines_all,
    retain_unique_values=[
        "type",
        "id_full",
        "capacity",
        "existing",
        "hp_type",
    ],
):
    """Simplify line network by dropping detours and removing useless forks.

    Parameters
    ----------
    lines_all : GeoDataFrame
        GeoDataFrame of lines to be simplified

    retain_unique_values : list, optional
        List of attributes of which unique values must be retained when
        simplifiying geometries. This means adjacent pipe segments are never
        merged if any values of the given attributes differ.

        Notes on the default selection:

            - ['type', 'id_full']: These are always created for new and
              existing pipes. Different types, i.e. distribution lines
              and building connection lines should never be merged, and
              ``id_full`` notes the name of the connected producer or consumer.
            - ['capacity', 'existing', 'hp_type']: These are the properties
              the user has to set when working with existing pipes, thus
              they need to remain intact.

        Selected attributes not present in the input data are silently ignored.

    Returns
    -------
    gdf_simple : GeoDataFrame
        Simplified line network.

    """
    retain_unique_values = [
        c for c in retain_unique_values if c in lines_all.columns
    ]

    edge_data_cols = ["length"]
    edge_data_cols.extend(retain_unique_values)
    cols = ["from_node", "to_node"] + edge_data_cols

    ebunch = [
        (a, b, dict(zip(edge_data_cols, values)))
        for a, b, *values in (
            lines_all[cols].itertuples(index=False, name=None)
        )
    ]

    graph = nx.Graph()
    graph.add_edges_from(ebunch)

    node_types = {
        node: {"type": node.split("-")[0][:-1]} for node in list(graph.nodes())
    }
    nx.set_node_attributes(graph, node_types)

    simplify_graph(graph=graph, retain_unique_values=retain_unique_values)

    lines_simplified = nx.to_pandas_edgelist(
        graph,
        source="from_node",
        target="to_node",
    )

    line_geometry = {}
    for i, line in lines_simplified.iterrows():
        if isinstance(line["path"], list):
            path_edges = [
                (n0, n1) for n0, n1 in zip(line["path"], line["path"][1:])
            ]
        else:
            path_edges = [(line["from_node"], line["to_node"])]
        lines_simplified.at[i, "path"] = path_edges
        line_geometry[i] = _line_string(path_edges, lines_all)

    lines_simplified["geometry"] = line_geometry

    # Line orientation needs to be redefined to match the new geometries
    lines_simplified["from_node"] = lines_simplified["path"].apply(
        lambda x: x[0][0]
    )
    lines_simplified["to_node"] = lines_simplified["path"].apply(
        lambda x: x[-1][-1]
    )

    # Drop temporary columns
    lines_simplified = lines_simplified.drop(columns=["path"], errors="ignore")

    gdf_simple = gpd.GeoDataFrame(lines_simplified, crs=lines_all.crs)
    gdf_simple.index.set_names(lines_all.index.names, inplace=True)

    logger.debug(
        "Simplified number of lines from {} to {}".format(
            len(lines_all), len(gdf_simple)
        )
    )

    return gdf_simple


def simplify_graph(
    graph: nx.Graph,
    retain_unique_values: list = [],
) -> bool:
    """Simplifies graph as much as possibe based on only local information.

    Parameters
    ----------
    graph : nx.Graph
        graph to be simplified.

    Returns
    -------
    bool
        True if the graph had to be simplified, false if it was already simple.
    """
    graph_was_updated = False
    graph_needs_iteration = True
    while graph_needs_iteration:
        graph_needs_iteration = False
        detours_dropped = _drop_detours(graph)
        forks_removed = _remove_useless_forks(
            graph, retain_unique_values=retain_unique_values
        )

        # if something changed, we need a new iteration
        graph_needs_iteration = detours_dropped or forks_removed

        # graph was updated if new iteration is needed or it was updated before
        graph_was_updated = graph_needs_iteration or graph_was_updated

    return graph_was_updated


def annotate_distance(
    graph: nx.Graph,
) -> None:
    """Inefficient algorithm that does the job."""
    for source in list(graph.nodes()):
        source_type = graph.nodes[source]["type"]
        for target in list(graph.nodes()):
            target_type = graph.nodes[target]["type"]
            if source_type != target_type:
                source_distance = graph.nodes[source].get("distance", math.inf)
                target_distance = graph.nodes[target].get("distance", math.inf)
                path_length = nx.shortest_path_length(
                    graph,
                    source=source,
                    target=target,
                    weight="length",
                )
                graph.nodes[source]["distance"] = min(
                    path_length, source_distance
                )
                graph.nodes[target]["distance"] = min(
                    path_length, target_distance
                )


def longest_distance(
    graph: nx.Graph,
) -> float:
    _longest_distance = 0.0
    for source in list(graph.nodes()):
        if graph.nodes[source]["type"] != "fork":
            for target in list(graph.nodes()):
                if graph.nodes[target]["type"] != "fork":
                    _longest_distance = max(
                        _longest_distance,
                        nx.shortest_path_length(
                            graph,
                            source=source,
                            target=target,
                            weight="length",
                        ),
                    )
    return _longest_distance


def _drop_detours(
    graph: nx.Graph,
) -> bool:
    graph_was_updated = False
    for source, target in list(graph.edges()):
        edge_length = graph[source][target]["length"]
        if edge_length > nx.shortest_path_length(
            graph,
            source=source,
            target=target,
            weight="length",
        ):
            graph.remove_edge(source, target)
            graph_was_updated = True

    return graph_was_updated


def _remove_useless_forks(
    graph: nx.Graph,
    retain_unique_values: list = [],
) -> bool:
    """Removes forks that only connect two lines as well as dead ends.

    You need to iterate to also remove forks
    that connected dead ends to meaningful lines.
    """
    graph_was_updated = False
    for node in list(graph.nodes()):
        if graph.nodes[node]["type"] == "fork":
            if graph.degree(node) == 1:
                graph.remove_node(node)
                graph_was_updated = True
            elif graph.degree(node) == 2:
                neighbors = tuple(graph.neighbors(node))
                edge0 = graph[neighbors[0]][node]
                edge1 = graph[node][neighbors[1]]

                # Do not merge if any retained attributes differ. If both
                # values of an attribute are NaN, merging is allowed
                def attrs_match(a, b):
                    return (pd.isna(a) and pd.isna(b)) or (a == b)

                if any(
                    not attrs_match(edge0.get(attr), edge1.get(attr))
                    for attr in retain_unique_values
                ):
                    continue

                edge_length = edge0["length"] + edge1["length"]
                path_left = edge0.get("path", [])
                if path_left:
                    if node == path_left[0]:
                        path_left = path_left[::-1]
                    path_left = path_left[:-1]
                else:
                    path_left = [neighbors[0]]

                path_right = edge1.get("path", [])
                if path_right:
                    if node == path_right[-1]:
                        path_right = path_right[::-1]
                    path_right = path_right[1:]
                else:
                    path_right = [neighbors[1]]

                path = path_left + [node] + path_right

                edge_attrs = {
                    attr: edge0.get(attr) for attr in retain_unique_values
                }

                existing_edge_data = graph.get_edge_data(*neighbors)
                if existing_edge_data is None:
                    # direct edge does not exist, yet
                    graph.add_edge(
                        neighbors[0],
                        neighbors[1],
                        length=edge_length,
                        path=path,
                        **edge_attrs,
                    )
                elif edge_length < existing_edge_data["length"]:
                    # direct edge already exists but is longer
                    edge_attrs["length"] = edge_length
                    edge_attrs["path"] = path
                    nx.set_edge_attributes(graph, edge_attrs)

                graph.remove_node(node)
                graph_was_updated = True
    return graph_was_updated


def check_crs(gdf, crs=4647, force_2d=True):
    """Convert CRS to EPSG:4647 - ETRS89 / UTM zone 32N (zE-N).

    This is the (only?) Coordinate Reference System that gives the correct
    results for distance calculations.

    Note about enforcing 2D geometries:

    Most underlying functions (e.g. distance measurement in shapely) do
    not support 3D geometries. Having z-coordinates in the
    data can cause issues in several places in the code, especially when
    e.g. buildings contain z coordinates, but streets do not.

    The savest option currently is to force 2d on all input geometries.

    Parameters
    ----------
    gdf : GeoDataFrame
        The GeoDataFrame to update.
    crs : int (optional)
        EPSG code for a coordinate reference system to convert to.
        Default is 4647.
    force_2d : boolean (optional)
        If True, enforce reduction of 3D geometry to 2D. Default is True.

    Returns
    -------
    gdf : GeoDataFrame
        Updated GeoDataFrame.


    """
    if gdf.crs.to_epsg() != crs:
        gdf.to_crs(epsg=crs, inplace=True)
        logger.info("CRS of GeoDataFrame converted to EPSG:{0}".format(crs))

    if force_2d and gdf.has_z.any():
        logger.debug("Reducing 3D geometry to 2D for compatibility")
        # Alternatively, use "gdf.force_2d()" with geopandas>0.14.3
        gdf.geometry = shapely.force_2d(gdf.geometry)  # requires shapely>=2.0

    return gdf

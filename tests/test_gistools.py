# -*- coding: utf-8 -*-
"""
These tests test if proper errors are raised when the data is not consistent,
of the wrong type or not all required data are given.

This file is part of project oemof (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/tools/helpers.py

SPDX-License-Identifier: MIT
"""

import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString
from shapely.geometry import MultiLineString
from shapely.geometry import Point

from dhnx.gistools import connect_points as cp
from dhnx.gistools import geometry_operations as go


def test_lot_foot_calc():
    point = Point([(0.5, 1)])
    line = LineString([(0, 0), (1, 1)])
    assert cp.calc_lot_foot(line, point) == Point([(0.75, 0.75)])


def test_split_linestring():
    line1 = LineString([(0, 0), (1, 3), (2, 0)])
    line2 = MultiLineString(
        lines=[line1, LineString([(5, 5), (7, 9), (3, 4)])]
    )
    line3 = LineString([(1, 1), (5, 1)])
    gdf_line = gpd.GeoDataFrame(geometry=[line1, line2, line3])
    results = go.split_multilinestr_to_linestr(gdf_line)
    assert gdf_line.geometry.length.sum() == results.length.sum()
    assert len(results.index) == 7


def test_drop_detours():
    edgelist = [
        (0, 1, {"weight": 5}),
        (1, 2, {"weight": 2}),
        (2, 0, {"weight": 2}),
    ]
    graph = nx.Graph(edgelist)

    go._drop_detours(graph)

    # longer connection with direct edge has been dropped
    assert list(graph.edges()) == [(0, 2), (1, 2)]


nodelist = [
    (0, {"type": "fork"}),
    (1, {"type": "fork"}),
    (2, {"type": "fork"}),
    (3, {"type": "fork"}),
    (4, {"type": "fork"}),
    ("s1", {"type": "sink"}),
    ("s2", {"type": "sink"}),
]
edgelist = [
    ("s1", 0, {"weight": 1}),
    (0, 1, {"weight": 5}),
    (1, 2, {"weight": 2}),
    (2, 4, {"weight": 7}),
    (2, 3, {"weight": 2}),
    ("s2", 3, {"weight": 1}),
]


def test_annotate_distance():
    graph = nx.Graph()
    graph.add_nodes_from(nodelist)
    graph.add_edges_from(edgelist)
    go.annotate_distance(graph)

    distances = {
        0: 1,
        1: 5,
        2: 3,
        3: 1,
        4: 10,
        "s1": 1,
        "s2": 1,
    }
    node_list = list(graph.nodes())
    for node in node_list:
        assert graph.nodes[node]["distance"] == distances[node]


def test_longest_distance():
    graph = nx.Graph()
    graph.add_nodes_from(nodelist)
    graph.add_edges_from(edgelist)

    assert go.longest_distance(graph) == 5 + 2 + 2 + 1 + 1


def test_remove_useless_forks():
    graph = nx.Graph()
    graph.add_nodes_from(nodelist)
    graph.add_edges_from(edgelist)
    graph_was_updated = go.simplify_graph(graph)

    assert graph_was_updated
    assert list(graph.edges()) == [("s1", "s2")]
    assert len(graph["s1"]["s2"]["via"]) == 5
    assert graph["s1"]["s2"]["weight"] == 1 + 5 + 2 + 2 + 1

geometry = [
    LineString([[1, 2], [1, 1]]),
    LineString([[1, 1], [2, 3]]),
    LineString([[2, 3], [1, 2]]),
    LineString([[3, 2], [1, 1]]),
    LineString([[2, 3], [4, 4]]),
]
from_node = ["forks-12", "forks-11", "forks-23", "forks-32", "forks-23"]
to_node = ["forks-11", "forks-23", "forks-12", "forks-11", "forks-44"]
length = [23, 13, 48, 4, 8]

lines_all = gpd.GeoDataFrame(
    {
        "from_node": from_node,
        "to_node": to_node,
        "length": length,
    },
    geometry=geometry,
)

def test_line_string():
    assert go._line_string(
        lines_all=lines_all,
        path_edges=[["forks-12", "forks-11"]],
    ) == geometry[0]

    assert (
        list(
            go._line_string(
                lines_all=lines_all,
                path_edges=[["forks-11", "forks-12"]],
            ).coords
        )
        == list(geometry[0].coords)[::-1]
    )

    ls = list(go._line_string(
            lines_all=lines_all,
            path_edges=[
                ["forks-12", "forks-11"],
                ["forks-11", "forks-23"],
                ["forks-23", "forks-44"],
            ],
        ).coords
    )
    assert len(ls) == 4
    assert ls == list(geometry[0].coords) + list(geometry[4].coords)

    ls = list(go._line_string(
            lines_all=lines_all,
            path_edges=[
                ["forks-12", "forks-11"],
                ["forks-23", "forks-11"],
                ["forks-23", "forks-44"],
            ],
        ).coords
    )
    assert len(ls) == 4
    assert ls == list(geometry[0].coords) + list(geometry[4].coords)

    ls = list(go._line_string(
            lines_all=lines_all,
            path_edges=[
                ["forks-12", "forks-23"],
                ["forks-23", "forks-11"],
                ["forks-11", "forks-32"],
            ],
        ).coords
    )
    assert len(ls) == 4

# -*- coding: utf-8 -*-
"""
These tests test if proper errors are raised when the data is not consistent,
of the wrong type or not all required data are given.

This file is part of project oemof (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/tools/helpers.py

SPDX-License-Identifier: MIT
"""

import os

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
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


def test_all_values_equal():

    assert go._all_values_equal(
        pd.Series([0, 0, 0]),
        ignore_nan=True,
    )

    assert go._all_values_equal(
        pd.Series([0, 0, 0]),
        ignore_nan=False,
    )

    assert not go._all_values_equal(
        pd.Series([0, 0, 1]),
        ignore_nan=True,
    )
    assert not go._all_values_equal(
        pd.Series([0, 0, 1]),
        ignore_nan=False,
    )

    assert go._all_values_equal(
        pd.Series([0, 0, np.nan]),
        ignore_nan=True,
    )

    assert not go._all_values_equal(
        pd.Series([0, 0, np.nan]),
        ignore_nan=False,
    )


def test_drop_detours():
    EDGELIST = [
        (0, 1, {"length": 5, "same": 0, "different": 1, "unique": 1}),
        (1, 2, {"length": 2, "same": 0, "different": 3}),
        (2, 0, {"length": 2, "same": 0, "different": 3}),
    ]
    graph = nx.Graph(EDGELIST)
    go._drop_detours(graph, [])
    assert list(graph.edges()) == [(0, 2), (1, 2)]

    graph = nx.Graph(EDGELIST)
    graph[0][1]['existing'] = 1
    go._drop_detours(graph, [])
    assert list(graph.edges()) == [(0, 1), (0, 2), (1, 2)]

    graph = nx.Graph(EDGELIST)
    graph[1][2]['existing'] = 1
    go._drop_detours(graph, [])
    assert list(graph.edges()) == [(0, 1), (0, 2), (1, 2)]

    graph = nx.Graph(EDGELIST)
    go._drop_detours(graph, ["same"])
    assert list(graph.edges()) == [(0, 2), (1, 2)]

    graph = nx.Graph(EDGELIST)
    go._drop_detours(graph, ["different"])
    assert list(graph.edges()) == [(0, 1), (0, 2), (1, 2)]

    graph = nx.Graph(EDGELIST)
    go._drop_detours(graph, ["unique"])
    assert list(graph.edges()) == [(0, 1), (0, 2), (1, 2)]


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
    ("s1", 0, {"length": 1}),
    (0, 1, {"length": 5}),
    (2, 1, {"length": 2}),
    (2, 4, {"length": 7}),
    (3, 2, {"length": 2}),
    ("s2", 3, {"length": 1}),
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


def test_simplify_graph():
    graph = nx.Graph()
    graph.add_nodes_from(nodelist)
    graph.add_edges_from(edgelist)
    graph_was_updated = go.simplify_graph(graph)

    assert graph_was_updated
    assert set(graph.edges()) == set([("s1", "s2")])
    assert len(graph["s1"]["s2"]["path"]) == 6
    assert graph["s1"]["s2"]["path"] == ["s1", 0, 1, 2, 3, "s2"]
    assert graph["s1"]["s2"]["length"] == 1 + 5 + 2 + 2 + 1


def test_simplify_graph_keep_unique():
    graph = nx.Graph()
    graph.add_nodes_from(nodelist)
    graph.add_edges_from(edgelist)
    graph[1][2]["unique"] = 5
    graph_was_updated = go.simplify_graph(graph, ["unique"])

    assert graph_was_updated
    assert set(graph.edges()) == set([(1, 2), (1, "s1"), (2, "s2")])


geometry = [
    LineString([[1, 2], [1, 1]]),
    LineString([[1, 1], [1.5, 1.5], [2, 3]]),
    LineString([[2, 3], [1, 2]]),
    LineString([[3, 2], [2, 1], [1, 1]]),
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
    assert len(ls) == 5
    assert ls == list(geometry[0].coords) + [(1.5, 1.5)] + list(
        geometry[4].coords
    )

    ls = list(go._line_string(
            lines_all=lines_all,
            path_edges=[
                ["forks-12", "forks-11"],
                ["forks-23", "forks-11"],
                ["forks-23", "forks-44"],
            ],
        ).coords
    )
    assert len(ls) == 5
    assert ls == list(geometry[0].coords) + [(1.5, 1.5)] + list(
        geometry[4].coords
    )

    ls = list(go._line_string(
            lines_all=lines_all,
            path_edges=[
                ["forks-12", "forks-23"],
                ["forks-23", "forks-11"],
                ["forks-11", "forks-32"],
            ],
        ).coords
    )
    assert len(ls) == 6


def test_remove_useless_forks_keeps_shortest():
    edgelist = [
        (
            "forks-176",
            "forks-170",
            {"length": 9, "type": "DL", "id_full": ""},
        ),
        (
            "forks-176",
            "forks-178",
            {"length": 36, "type": "DL", "id_full": ""},
        ),
        (
            "forks-178",
            "forks-182",
            {"length": 16, "type": "DL", "id_full": ""},
        ),
        (
            "forks-178",
            "forks-183",
            {"length": 65, "type": "DL", "id_full": ""},
        ),
        (
            "forks-178",
            "consumers-10",
            {
                "length": 23,
                "type": "HL",
                "id_full": "consumers-10",
            },
        ),
        (
            "forks-182",
            "forks-184",
            {"length": 14, "type": "DL", "id_full": ""},
        ),
        (
            "forks-182",
            "forks-185",
            {"length": 61, "type": "DL", "id_full": ""},
        ),
        (
            "forks-183",
            "forks-185",
            {"length": 16, "type": "DL", "id_full": ""},
        ),
        (
            "forks-184",
            "forks-187",
            {"length": 9, "type": "DL", "id_full": ""},
        ),
        (
            "forks-184",
            "consumers-44",
            {
                "length": 14,
                "type": "HL",
                "id_full": "consumers-44",
            },
        ),
    ]

    graph = nx.Graph()
    graph.add_edges_from(edgelist)
    node_types = {
        node: {"type": node.split("-")[0][:-1]} for node in list(graph.nodes())
    }
    nx.set_node_attributes(graph, node_types)

    forks_removed = go._remove_useless_forks(graph, [])

    assert forks_removed
    # There is an alterantive connection between the two nodes.
    # We make sure the shorter one is kept.
    assert graph["forks-178"]["forks-182"]["length"] == 16


def test_process_geometry():
    """Test ``process_geometry()`` function with a simple example.

    It includes pipes with ``existing=1``, due to which an otherwise
    deleted detour must be kept.
    """
    base_dir = os.path.join(
        os.path.dirname(__file__), "_files/process_geometry"
    )
    gdf_lines = gpd.read_file(
        os.path.join(base_dir, "in/lines_input_existing.geojson")
    )
    gdf_prod = gpd.read_file(
        os.path.join(base_dir, "in/producers_polygon.geojson")
    )
    gdf_cons = gpd.read_file(
        os.path.join(base_dir, "in/consumers_polygon.geojson")
    )
    file_pipes = os.path.join(base_dir, "out/pipes.geojson")
    os.makedirs(os.path.dirname(file_pipes), exist_ok=True)

    tn_input = cp.process_geometry(
        lines=gdf_lines,
        producers=gdf_prod,
        consumers=gdf_cons,
        method="boundary",
        reset_index=True,
        welding=True,
    )

    assert tn_input["pipes"].crs is not None
    assert [c in tn_input["pipes"].columns for c in ["type", "id_full"]]
    assert tn_input["pipes"].index.name == "id"

    tn_input["pipes"] = tn_input["pipes"][sorted(tn_input["pipes"].columns)]
    tn_input["pipes"] = tn_input["pipes"].round(5)

    # Update expected result (after intentional changes)
    # tn_input["pipes"].to_file(file_pipes)

    # Load expected result (and fix column order)
    gdf_pipes_test = (
        gpd.read_file(file_pipes)
        .set_index("id")
        .reindex(tn_input["pipes"].columns, axis="columns")
    )

    assert (gdf_pipes_test.columns == tn_input["pipes"].columns).all()

    # Compare with tolerance, due to loss of floating point precision
    for col in tn_input["pipes"].columns:
        if col == tn_input["pipes"].geometry.name:
            assert gdf_pipes_test.geom_equals_exact(
                tn_input["pipes"], tolerance=1e-7
            ).all()
        else:
            assert gdf_pipes_test[[col]].equals(tn_input["pipes"][[col]])

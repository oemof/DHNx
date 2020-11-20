# -*- coding: utf-8 -*-
"""
These tests test if proper errors are raised when the data is not consistent, of the
wrong type or not all required data are given.

This file is part of project oemof (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/tools/helpers.py

SPDX-License-Identifier: MIT
"""
import pytest
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from shapely.geometry import Point

from dhnx.gistools import connect_points as cp
from dhnx.gistools import geometry_operations as go


def test_linestring_error():
    with pytest.raises(ValueError, match=r"The Linestrings must consists of simple lines"):
        line = LineString([(0, 0), (1, 2 / 3), (2, 0)])
        point = Point([(1, 1)])
        gdf_line = gpd.GeoDataFrame(geometry=[line])
        gdf_point = gpd.GeoDataFrame(geometry=[point])
        cp.create_object_connections(gdf_point, gdf_line)


def test_lot_foot_calc():
    point = Point([(0.5, 1)])
    line = LineString([(0, 0), (1, 1)])
    assert cp.calc_lot_foot(line, point) == Point([(0.75, 0.75)])


def test_split_linestring():
    line1 = LineString([(0, 0), (1, 3), (2, 0)])
    line2 = MultiLineString(lines=[line1, LineString([(5, 5), (7, 9), (3, 4)])])
    line3 = LineString([(1, 1), (5, 1)])
    gdf_line = gpd.GeoDataFrame(geometry=[line1, line2, line3])
    results = go.split_multilinestr_to_linestr(gdf_line)
    assert gdf_line.geometry.length.sum() == results.length.sum()
    assert len(results.index) == 7

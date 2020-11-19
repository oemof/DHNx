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
from shapely.geometry import LineString
from shapely.geometry import Point

from dhnx.gistools import connect_points as cp

def test_linestring_error():
    with pytest.raises(ValueError, match=r"The Linestrings must consists of simple lines"):
        line = LineString([(0, 0), (1, 2 / 3), (2, 0)])
        point = Point([(1, 1)])
        gdf_line = gpd.GeoDataFrame(geometry=[line])
        gdf_point = gpd.GeoDataFrame(geometry=[point])
        cp.create_object_connections(gdf_point, gdf_line)

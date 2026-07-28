# -*- coding: utf-8 -*-
"""
Test the complete investment optimization workflow of DHNx.

This file is part of project oemof (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/tools/helpers.py

SPDX-License-Identifier: MIT
"""
import io
import os

import geopandas as gpd
import numpy as np
import pandas as pd
from geopandas.testing import assert_geodataframe_equal

import dhnx


def get_default_dhnx_invest_options():
    """Generate a dictionary with default investments options for DHNx."""
    consumers_bus = """
label_2,active,excess,shortage,shortage costs,excess costs
heat,1,0,0,999999,9999
"""
    consumers_demand = """
label_2,active,nominal_capacity
heat,1,1
"""
    producers_bus = """
,label_2,active,excess,shortage,shortage costs,excess costs
1,heat,1,0,0,9999,9999
"""
    producers_source = """
label_2,active
heat,1
"""
    network = """
label_3,nonconvex,l_factor,l_factor_fix,cap_min,cap_max,capex_pipes,fix_costs
pipe-typ-A,1,1.5812551e-07,0.0221164,1,519307.085403,0.02908927,948.69105059
"""

    invest_options = dict(
        consumers=dict(
            bus=pd.read_csv(io.StringIO(consumers_bus)),
            demand=pd.read_csv(io.StringIO(consumers_demand)),
        ),
        producers=dict(
            bus=pd.read_csv(io.StringIO(producers_bus)),
            source=pd.read_csv(io.StringIO(producers_source)),
        ),
        network=dict(pipes=pd.read_csv(io.StringIO(network))),
    )
    return invest_options


def test_optimization_example_01():
    """Test ``optimize_investment()`` function with a simple example.

    It includes pipes with ``existing=1``, which is supposed to cover
    certain edge cases in the optimization workflow.
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
    file_pipes = os.path.join(base_dir, "out/pipes_result.geojson")
    os.makedirs(os.path.dirname(file_pipes), exist_ok=True)

    tn_input = dhnx.gistools.connect_points.process_geometry(
        lines=gdf_lines,
        producers=gdf_prod,
        consumers=gdf_cons,
        method="boundary",
        reset_index=True,
        simplify=True,
    )

    # initialize a ThermalNetwork
    network = dhnx.network.ThermalNetwork()

    # add the pipes, forks, consumer, and producers to the ThermalNetwork
    for k, v in tn_input.items():
        network.components[k] = v

    # check if ThermalNetwork is consistent
    network.is_consistent()

    # load the specification of the oemof-solph components
    invest_opt = get_default_dhnx_invest_options()

    settings = dict(
        solve_kw={"tee": False},  # Hide solver output
        return_existing=True,  # Include existing pipes in results
    )

    # Perform the investment optimisation
    network.optimize_investment(invest_options=invest_opt, **settings)

    results_edges = network.results.optimization["components"]["pipes"]
    gdf_pipes = network.components["pipes"].copy()
    cols_drop = [c for c in results_edges.columns if c in gdf_pipes]
    gdf_pipes = gdf_pipes.drop(columns=cols_drop)  # Drop duplicate columns
    gdf_pipes = gdf_pipes.join(results_edges, rsuffix="_results")
    gdf_pipes = gdf_pipes[gdf_pipes["capacity"] > 0]  # Keep only DN>0

    gdf_pipes = gdf_pipes.round(5)  # Round for comparison

    # Update expected result (after intentional changes)
    # gdf_pipes.to_file(file_pipes)

    # Load expected result (and fix column order)
    gdf_pipes_test = (
        gpd.read_file(file_pipes)
        .set_index("id")
        .reindex(gdf_pipes.columns, axis="columns")
        .replace({None: np.nan})
    )

    assert_geodataframe_equal(
        gdf_pipes,
        gdf_pipes_test,
        check_dtype=False,  # dtype changes after reading file
        check_index_type=False,  # dtype changes after reading file
        check_column_type=False,  # dtype changes after reading file
        check_less_precise=True,  # Required due to floating point precision
    )

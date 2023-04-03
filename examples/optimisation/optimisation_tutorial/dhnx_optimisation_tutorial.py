# -*- coding: utf-8 -*-

"""
Create a district heating network from OpenStreetMap data,
and perform a DHS Investment Optimisation.
Based on the routing and dimensioning of the optimisation, a pandapipes
model is generated for the detailed thermo-hydraulic calculation for
checking the feasibility of the suggested design of the optimisation.

Overview
--------

Optimisation
^^^^^^^^^^^^

Part I: Get and prepare the input data for the optimisation
    a) Geometry of potential routes and buildings
        - Get OSM data
        - Process the geometry for DHNx
    b) Pre-calculate the hydraulic parameter

Part II: Initialise the ThermalNetwork and perform the Optimisation

Part III: Postprocessing

Simulation
^^^^^^^^^^

Part I: Create panda-pipes model


Contributors:
- Joris Zimmermann
- Johannes Röder
"""
import numpy as np
import osmnx as ox
from shapely import geometry
import matplotlib.pyplot as plt

import logging
from oemof.tools import logger

from dhnx.network import ThermalNetwork
from dhnx.input_output import load_invest_options
from dhnx.gistools.connect_points import process_geometry

logger.define_logging(
    screen_level=logging.INFO,
    logfile="dhnx.log"
)

# # Part I: Get and prepare the input data for the optimisation

# ## a) Geometry of potential routes and buildings

# ### Get OSM data

# If you do not have any geo-referenced data, you can obtain the footprints
# and the street network as potential routes for the DHS from OpenStreetMaps.
# This is done with the library osmnx.

# Alternatively, you can of course use your individual GIS data.
# With geopandas, you can easily import different formats as .shp, .geojson
# or other GIS formats.
# The workflow could also use the OSM data as starting point,
# then you could manually edit the geometries, e.g. in QGIS,
# and the import them again in your Python script with geopandas.

# For getting the OSM data, first, select the street types you want to
# consider as routes for the district heating network.
# see also: https://wiki.openstreetmap.org/wiki/Key:highway

streets = dict({
    'highway': [
        'residential',
        'service',
        'unclassified',
    ]
})

# And also select the building types you want to import
# see: https://wiki.openstreetmap.org/wiki/Key:building

buildings = dict({
    'building': [
        'apartments',
        'commercial',
        'detached',
        'house',
        'industrial',
        'residential',
        'retail',
        'semidetached_house'
    ]
})

# Then, define a bounding box polygon from a list of lat/lon coordinates, that
# contains the district you are considering.

bbox = [(9.1008896, 54.1954005),
        (9.1048374, 54.1961024),
        (9.1090996, 54.1906397),
        (9.1027474, 54.1895923),
        ]
polygon = geometry.Polygon(bbox)

# With osmnx we can convert create a graph from the street network and
# plot this with the plotting function of osmnx

graph = ox.graph_from_polygon(polygon, network_type='drive_service')
ox.plot_graph(graph)

# Next, we create geopandas dataframes with the footprints of the buildings
# (polygon geometries) and also for the street network, which are line
# geometries

gdf_poly_houses = ox.geometries_from_polygon(polygon, tags=buildings)
gdf_lines_streets = ox.geometries_from_polygon(polygon, tags=streets)

# We need to make sure that only polygon geometries are used

gdf_poly_houses = gdf_poly_houses[gdf_poly_houses['geometry'].apply(
    lambda x: isinstance(x, geometry.Polygon)
)].copy()

# Remove nodes column (that make somehow trouble for exporting .geojson)

gdf_poly_houses.drop(columns=['nodes'], inplace=True)
gdf_lines_streets.drop(columns=['nodes'], inplace=True)

# We need one (or more) buildings that we call "generators", that represent
# the heat supply facility. In this example, we randomly choose one of the
# buildings and put it to a new GeoDataFrame. Of course, in your project,
# you need to import a geopandas DataFrame with you heat supply sites.

np.random.seed(42)
id_generator = np.random.randint(len(gdf_poly_houses))
gdf_poly_gen = gdf_poly_houses.iloc[[id_generator]].copy()
gdf_poly_houses.drop(index=gdf_poly_houses.index[id_generator], inplace=True)

# The houses need a maximum thermal power. For this example, we set it
# to a random value between 10 and 50 kW for all houses.
# Note: You can also provide the heat demand as demand time series.

gdf_poly_houses['P_heat_max'] = \
    np.random.randint(10, 50, size=len(gdf_poly_houses))

# Now, let's plot the given geometry with matplotlib

fig, ax = plt.subplots()
gdf_lines_streets.plot(ax=ax, color='blue')
gdf_poly_gen.plot(ax=ax, color='orange')
gdf_poly_houses.plot(ax=ax, color='green')
plt.title('Geometry before processing')
plt.show()

# You can optionally export the geometry (e.g. for QGIS) as follows:

# gdf_poly_houses.to_file('footprint_buildings.geojson', driver='GeoJSON')

# ### Process the geometry for DHNx

# Note: if you use your individual geometry layers, you must make sure, that
# the geometries of the lines are line geometries. And the geometries of the
# buildings and generators are either polygon or point geometries.

# if you are using your individual geometries,
# load your geopandas DataFrames:

# gdf_lines_streets = gpd.read_file('your_file.geojson')
# gdf_poly_gen = gpd.read_file('your_file.geojson')
# gdf_poly_houses = gpd.read_file('your_file.geojson')

# The next step is the processing of the geometries with DHNx.
# This function connects the consumers and producers to the line network
# by creating the connection lines to the buildings,
# and sets IDs for each building/segment.
# For connecting the polygons (in case you have polygons) to the street
# network, you can choose between two methods: connect to the midpoint of the
# polygon, or to the boundary of the polygon.

tn_input = process_geometry(
    lines=gdf_lines_streets,
    producers=gdf_poly_gen,
    consumers=gdf_poly_houses,
    method="boundary",  # select the method of how to connect the buildings
)

# The result of the processing are a dictionary with four geoDataFrames:
# consumers, producers, pipes and forks.
# After successfully processing, we can plot the geometry after processing.

_, ax = plt.subplots()
tn_input['consumers'].plot(ax=ax, color='green')
tn_input['producers'].plot(ax=ax, color='red')
tn_input['pipes'].plot(ax=ax, color='blue')
tn_input['forks'].plot(ax=ax, color='grey')
plt.title('Geometry after processing')
plt.show()

# Optionally export the geo dataframes and load it into QGIS or any other GIS
# Software for checking the results of the processing.

# path_geo = 'qgis'
# for key, val in tn_input.items():
#     val.to_file(os.path.join(path_geo, key + '.geojson'), driver='GeoJSON')


# ## b) Pre-calculate the hydraulic parameter

# Besides the geometries, we need the techno-economic data for the
# investment optimisation of the DHS piping network. Therefore, we load
# the pipes data table. This is the information you need to get from your
# manufacturer / from your project.



# Part III: Initialise the ThermalNetwork and perform the Optimisation #######

# initialize a ThermalNetwork
network = ThermalNetwork()

# add the pipes, forks, consumer, and producers to the ThermalNetwork
for k, v in tn_input.items():
    network.components[k] = v

# check if ThermalNetwork is consistent
network.is_consistent()

# load the specification of the oemof-solph components
invest_opt = load_invest_options('invest_data')


# optionally, define some settings for the solver. Especially increasing the
# solution tolerance with 'ratioGap' or setting a maximum runtime in 'seconds'
# helps if large networks take too long to solve
settings = dict(solver='cbc',
                solve_kw={
                    'tee': False,  # print solver output
                },
                solver_cmdline_options={
                    # 'allowableGap': 1e-5,  # (absolute gap) default: 1e-10
                    # 'ratioGap': 0.2,  # (0.2 = 20% gap) default: 0
                    # 'seconds': 60 * 1,  # (maximum runtime) default: 1e+100
                },
                )

# perform the investment optimisation
network.optimize_investment(invest_options=invest_opt, **settings)


# Part IV: Check the results #############

# get results
results_edges = network.results.optimization['components']['pipes']
# print(results_edges[['from_node', 'to_node', 'hp_type', 'capacity',
#                      'direction', 'costs', 'losses']])

print(results_edges[['costs']].sum())
print('Objective value: ', network.results.optimization['oemof_meta']['objective'])
# (The costs of the objective value and the investment costs of the DHS
# pipelines are the same, since no additional costs (e.g. for energy sources)
# are considered in this example.)

# add the investment results to the geoDataFrame
gdf_pipes = network.components['pipes']
gdf_pipes = gdf_pipes.join(results_edges, rsuffix='results_')

# plot output after processing the geometry
_, ax = plt.subplots()
network.components['consumers'].plot(ax=ax, color='green')
network.components['producers'].plot(ax=ax, color='red')
network.components['forks'].plot(ax=ax, color='grey')
gdf_pipes[gdf_pipes['capacity'] > 0].plot(ax=ax, color='blue')
plt.title('Invested pipelines')
plt.show()

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

Part II: Perform the Optimisation
    a) Initialise the ThermalNetwork and check input
    b) Perform the optimisation
    c) Process the results

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
import pandas as pd
from shapely import geometry
import matplotlib.pyplot as plt

import logging
from oemof.tools import logger

from dhnx.network import ThermalNetwork
from dhnx.input_output import load_invest_options
from dhnx.gistools.connect_points import process_geometry
from dhnx.optimization.precalc_hydraulic import v_max_bisection,\
    calc_mass_flow, calc_power, v_max_secant, calc_pipe_loss

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
# the pipes data table. This is the information you need from your
# manufacturer / from your project.

df_pipe_data = pd.read_csv("input/Pipe_data.csv", sep=",")
print(df_pipe_data.head(n=8))

# This is an example of input data. The Roughness refers to the roughness of
# the inner surface and depends on the material (steel, plastic). The U-value
# and the costs refer to the costs of the whole pipeline trench, so including
# forward and return pipelines. The design process of DHNx is based on
# a maximum pressure drop per meter as design criteria:

df_pipe_data["Maximum pressure drop [Pa/m]"] = 150

# You could also define the maximum pressure drop individually for each DN
# number.

# As further assumptions, you need to estimate the operation temperatures of
# the district heating network in the design case:

df_pipe_data["T_forward [C]"] = 80
df_pipe_data["T_return [C]"] = 50
df_pipe_data["T_level [C]"] = 65

# Based on that pressure drop, the maximum transport capacity (mass flow) is
# calculated for each DN number.

# First, the maximum flow velocity is calculated.

df_pipe_data["v_max [m/s]"] = df_pipe_data.apply(lambda row: v_max_bisection(
    d_i=row["Inner diameter [m]"],
    T_average=row["T_level [C]"],
    k=row['Roughness [mm]'],
    p_max=row["Maximum pressure drop [Pa/m]"]), axis=1)

# Then, the maximum mass flow:

df_pipe_data['Mass flow [kg/s]'] = df_pipe_data.apply(
    lambda row: calc_mass_flow(
        v=row['v_max [m/s]'],
        di=row["Inner diameter [m]"],
        T_av=row["T_level [C]"]), axis=1,
)

# Finally, the maximum thermal transport capacity of each DN pipeline trench
# in kW is calculated based on the design temperatures of the DHS:

df_pipe_data['P_max [kW]'] = df_pipe_data.apply(
    lambda row: 0.001 * calc_power(
        T_vl=row['T_forward [C]'],
        T_rl=row['T_return [C]'],
        mf=row['Mass flow [kg/s]']), axis=1,
)

# Furthermore, the thermal loss of ech DN number per meter is calculated
# (based on the design temperatures of the district heating network):

temperature_ground = 10

df_pipe_data['P_loss [kW]'] = df_pipe_data.apply(
    lambda row: 0.001 * calc_pipe_loss(
        temp_average=row["T_level [C]"],
        u_value=row["U-value [W/mK]"],
        temp_ground=temperature_ground,
    ), axis=1,
)

# The last step is the linearisation of the cost  and loss parameter for the
# DHNx optimisation (which is based on the MILP optimisation package
# oemof-solph)

# It is possible to use different accuracies: you could linearize the cost
# and loss values with 1 segment, or many segment, or you can also perform
# an optimisation with discrete DN numbers (which is of course computationally
# more expensive). See also the DHNx example "discrete_DN_numbers"

# Here follows a linear approximation with 1 segment

constants_costs = np.polyfit(
    df_pipe_data['P_max [kW]'], df_pipe_data['Costs [eur]'], 1,
)
constants_loss = np.polyfit(
    df_pipe_data['P_max [kW]'], df_pipe_data['P_loss [kW]'], 1,
)

print('Costs constants: ', constants_costs)
print('Loss constants: ', constants_loss)

# Let's plot the economic assumptions:

x_min = df_pipe_data['P_max [kW]'].min()
x_max = df_pipe_data['P_max [kW]'].max()
y_min = constants_costs[0] * x_min + constants_costs[1]
y_max = constants_costs[0] * x_max + constants_costs[1]

_, ax = plt.subplots()
x = df_pipe_data['P_max [kW]']
y = df_pipe_data['Costs [eur]']
ax.plot(x, y, lw=0, marker="o", label="DN numbers",)
ax.plot(
    [x_min, x_max], [y_min, y_max],
    ls=":", color='r', marker="x"
)
ax.set_xlabel("Transport capacity [kW]")
ax.set_ylabel("Kosten [€/m]")
plt.text(
    2000, 250,
    "Linear cost approximation \n"
    "of district heating pipelines \n"
    "based on maximum pressure drop \n"
    "of {:.0f} Pa/m".format(df_pipe_data["Maximum pressure drop [Pa/m]"][0])
)
plt.legend()
plt.ylim(0, None)
plt.grid(ls=":")
plt.show()

# The next step is the creation of the input dataframe with the techno-economic
# parameter of the district heating pipelines (See DHNx documentation).

# Note: you can also skip the previous pre-calculation of the hydraulic
# parameter and directly fill the following table with the optimisation
# parameter of the district heating pipelines.

df_pipes = pd.DataFrame(
    {
        "label_3": "your-pipe-type-label",
        "active": 1,
        "nonconvex": 1,
        "l_factor": constants_loss[0],
        "l_factor_fix": constants_loss[1],
        "cap_max": df_pipe_data['P_max [kW]'].max(),
        "cap_min": df_pipe_data['P_max [kW]'].min(),
        "capex_pipes": constants_costs[0],
        "fix_costs": constants_costs[1],
    }, index=[0],
)

# Export the optimisation parameter of the dhs pipelines to the investment
# data and replace the default csv file.

df_pipes.to_csv(
    "invest_data/network/pipes.csv", index=False,
)

# #############################################################################

# # Part II: Perform the Optimisation

# ## a) Initialise the ThermalNetwork and check input

network = ThermalNetwork()

# Add the pipes, forks, consumer, and producers as components
# to the ThermalNetwork

for k, v in tn_input.items():
    network.components[k] = v

# Check if ThermalNetwork is consistent

network.is_consistent()

# Important: Check if geometry is connected with networknx.
# It sometimes happens that two lines in your input geometry are not connected,
# because the starting point of one line is not exactly the ending point of
# the other line.

import networkx as nx

network.nx_graph = network.to_nx_undirected_graph()
g = network.nx_graph
nx.is_connected(g)

# If `nx.is_connected(g)` returns false, you can use the following lines
# to find out of how many networks your geometry consists, and which ids
# belong to these networks. With this information, load your geometry in QGIS
# and manually fix the geometry.

# Number of networks
print(len(sorted(nx.connected_components(g), key=len, reverse=True)))

# Components of the network
print([c for c in sorted(nx.connected_components(g), key=len, reverse=True)])

# Now, we have all data collected and checked, and we continue with the DHNx
# investment optimisation

# Now, we load the whole specification for the oemof-solph components from
# the invest_data folder, in which we previously exported the specifications
# for the dhs pipelines

invest_opt = load_invest_options('invest_data')

# With the optimisation settings, you can e.g. configure the solver.
# Especially increasing the solution tolerance with 'ratioGap'
# or setting a maximum runtime in 'seconds' helps if large networks take
# too long to solve.
# Please see :func::dhnx.optimisation_models.setup_optimise_investment: for
# all options.

settings = dict(solver='cbc',
                solve_kw={
                    'tee': True,  # print solver output
                },
                solver_cmdline_options={
                    # 'allowableGap': 1e-5,  # (absolute gap) default: 1e-10
                    # 'ratioGap': 0.2,  # (0.2 = 20% gap) default: 0
                    # 'seconds': 60 * 1,  # (maximum runtime) default: 1e+100
                },
                )

# ## b) Perform the optimisation

# Now, we execute the actual optimisation

network.optimize_investment(invest_options=invest_opt, **settings)

# ## c) Process the results

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

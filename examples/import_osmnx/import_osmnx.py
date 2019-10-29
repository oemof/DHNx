import os

import geopandas as gpd
import matplotlib.pyplot as plt
import osmnx as ox
import pandas as pd

import district_heating_simulation as dhs
from shapely.ops import nearest_points
from shapely.geometry import LineString


# load street network and footprints from osm
place_name = '52.43034,13.53806'
distance = 300
file_name = '_'.join(place_name.split(','))

if not os.path.exists(f'data/{file_name}.graphml'):

    print('Download street network')

    graph = ox.graph_from_address(place_name, distance=distance)

    ox.save_load.save_graphml(graph, filename=f'{file_name}.graphml')

if not os.path.exists(f'data/{file_name}_footprints'):

    print('Download footprints')

    footprints = ox.footprints.footprints_from_address(place_name, distance=distance)

    footprints_proj = ox.project_gdf(footprints)

    footprints_save = footprints.drop(labels='nodes', axis=1)

    footprints_save.to_file(f'data/{file_name}_footprints')

# load network and footprints from disk
graph = ox.save_load.load_graphml(f'{file_name}.graphml')

graph = ox.project_graph(graph)

footprints = gpd.read_file(f'data/{file_name}_footprints')

footprints = ox.project_gdf(footprints)

# get building data
areas = footprints.area

# get nodes and edges from graph
nodes, edges = ox.save_load.graph_to_gdfs(graph)

nodes = nodes.loc[:, ['x', 'y', 'geometry']].reset_index()
replace_ids = {v: k for k, v in dict(nodes.loc[:, 'index']).items()}
nodes = nodes.drop('index', 1)

edges = edges.loc[:, ['u', 'v', 'geometry']]
edges.loc[:, ['u', 'v']] = edges.loc[:, ['u', 'v']].replace(replace_ids)


def connect_points_to_network(points, nodes, edges):
    r"""

    Parameter
    ---------
    points :

    nodes : geopandas.GeoDataFrame
        Nodes of the network

    edges : geopandas.GeoDataFrame
        Edges of the network

    Returns
    -------
    points :
    nodes :
    edges :
    """
    edges_united = edges.unary_union

    len_nodes = len(nodes)
    len_points = len(points)

    # assign ids to new points
    n_points = []
    n_nearest_points = []
    n_edges = []

    for i, point in enumerate(points.geometry):
        id_nearest_point = len_nodes + i

        id_point = len_nodes + len_points + i

        nearest_point = nearest_points(edges_united, point)[0]

        n_points.append([id_point, point.x, point.y, point])

        n_nearest_points.append([id_nearest_point, nearest_point.x, nearest_point.y, nearest_point])

        n_edges.append([id_point, id_nearest_point, LineString([point, nearest_point])])

    n_points = gpd.GeoDataFrame(
        n_points,
        columns=['index', 'x', 'y', 'geometry']).set_index('index')

    n_nearest_points = gpd.GeoDataFrame(
        n_nearest_points,
        columns=['index', 'x', 'y', 'geometry']).set_index('index')

    n_edges = gpd.GeoDataFrame(n_edges, columns=['u', 'v', 'geometry'])

    joined_nodes = pd.concat([nodes, n_nearest_points], sort=True)
    joined_edges = pd.concat([edges, n_edges], sort=True)

    return n_points, joined_nodes, joined_edges


building_midpoints = gpd.GeoDataFrame(footprints.geometry.centroid, columns=['geometry'])
building_midpoints['x'] = building_midpoints.apply(lambda x: x.geometry.x, 1)
building_midpoints['y'] = building_midpoints.apply(lambda x: x.geometry.y, 1)
building_midpoints = building_midpoints[['x', 'y', 'geometry']]

points, splits, edges = connect_points_to_network(building_midpoints, nodes, edges)

producer = points.loc[[323], :]
consumer = points.drop(323)

# save files
if not os.path.isdir(os.path.join('data', file_name)):
    os.makedirs(os.path.join('data', file_name))

producer.to_file(os.path.join('data', file_name, 'producer.shp'))
consumer.to_file(os.path.join('data', file_name, 'consumer.shp'))
splits.to_file(os.path.join('data', file_name, 'splits.shp'))
edges.to_file(os.path.join('data', file_name, 'edges.shp'))

# plot
fig, ax = plt.subplots()
producer.plot(ax=ax, color='r')
consumer.plot(ax=ax, color='g')

for x, y, label in zip(points.geometry.x, points.geometry.y, points.index):
    ax.annotate(label, xy=(x, y),
                xytext=(3, 3),
                textcoords='offset points',
                alpha=.3)

for x, y, label in zip(nodes.geometry.x, nodes.geometry.y, nodes.index):
    ax.annotate(label, xy=(x, y),
                xytext=(3, 3),
                textcoords='offset points',
                alpha=.3)

splits.plot(ax=ax)
edges.plot(ax=ax)
footprints.plot(ax=ax, alpha=.3)
plt.show()

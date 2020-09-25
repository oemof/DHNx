import os

import geopandas as gpd
import matplotlib.pyplot as plt

try:
    import osmnx as ox
except ImportError:
    print("Need to install osmnx to run this example")

from dhnx.dhn_from_osm import connect_points_to_network


# load street network and footprints from osm
place_name = (52.43034, 13.53806)
distance = 300
file_name = 'Berlin-Adlershof'

if not os.path.exists(f'data/{file_name}_street_network.graphml'):

    print('Download street network')

    graph = ox.graph_from_point(place_name, distance=distance)

    ox.save_load.save_graphml(graph, filename=f'{file_name}_street_network.graphml')

if not os.path.exists(f'data/{file_name}_footprints'):

    print('Download footprints')

    footprints = ox.footprints.footprints_from_point(place_name, distance=distance)

    footprints_proj = ox.project_gdf(footprints)

    footprints_save = footprints.drop(labels='nodes', axis=1)

    footprints_save.to_file(f'data/{file_name}_footprints')

# load network and footprints from disk
graph = ox.save_load.load_graphml(f'{file_name}_street_network.graphml')

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

building_midpoints = gpd.GeoDataFrame(footprints.geometry.centroid, columns=['geometry'])
building_midpoints['x'] = building_midpoints.apply(lambda x: x.geometry.x, 1)
building_midpoints['y'] = building_midpoints.apply(lambda x: x.geometry.y, 1)
building_midpoints = building_midpoints[['x', 'y', 'geometry']]

points, forks, pipes = connect_points_to_network(
    building_midpoints, nodes, edges)

# choose one of the points to be a producer
producer_id = 469

producers = points.loc[[producer_id], :]

consumers = points.drop(producer_id)

# save files
if not os.path.isdir(os.path.join('data', f'{file_name}_potential_dhn')):
    os.makedirs(os.path.join('data', f'{file_name}_potential_dhn'))

producers.to_file(os.path.join('data', f'{file_name}_potential_dhn', 'producer.shp'))
consumers.to_file(os.path.join('data', f'{file_name}_potential_dhn', 'consumer.shp'))
forks.to_file(os.path.join('data', f'{file_name}_potential_dhn', 'forks.shp'))
pipes.to_file(os.path.join('data', f'{file_name}_potential_dhn', 'pipes.shp'))

# plot
fig, ax = plt.subplots()
producers.plot(ax=ax, color='r')
consumers.plot(ax=ax, color='g')

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

forks.plot(ax=ax)
pipes.plot(ax=ax)
footprints.plot(ax=ax, alpha=.3)
plt.show()

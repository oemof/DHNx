import os

import geopandas as gpd
import matplotlib.pyplot as plt
import osmnx as ox
import pandas as pd

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

if not os.path.exists(f'{file_name}_footprints'):

    print('Download footprints')

    footprints = ox.footprints.footprints_from_address(place_name, distance=distance)

    footprints_proj = ox.project_gdf(footprints)

    footprints_save = footprints.drop(labels='nodes', axis=1)

    footprints_save.to_file(f'{file_name}_footprints')

# load network and footprints from disk
graph = ox.save_load.load_graphml(f'{file_name}.graphml')

graph = ox.project_graph(graph)

footprints = gpd.read_file(f'{file_name}_footprints')

footprints = ox.project_gdf(footprints)

# get building data
areas = footprints.area


def connect_points_to_network(graph, points):
    r"""

    Parameter
    ---------
    graph :
    points :
    Returns
    -------
    new_graph :
    """
    nodes, edges = ox.save_load.graph_to_gdfs(graph)

    nodes = nodes.loc[:, ['x', 'y', 'geometry']].reset_index()
    replace_ids = {v: k for k, v in dict(nodes.loc[:, 'index']).items()}
    nodes = nodes.drop('index', 1)

    edges = edges.loc[:, ['u', 'v', 'geometry']]
    edges.loc[:, ['u', 'v']] = edges.loc[:, ['u', 'v']].replace(replace_ids)

    edges_united = edges.unary_union

    len_nodes = len(nodes)
    len_points = len(points)

    # assign ids to new points
    n_points = []
    n_nearest_points = []
    n_edges = []

    for i, point in enumerate(points.geometry):
        id_point = len_nodes + i

        id_nearest_point = len_nodes + len_points + i

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

    print(nodes.head())
    print(edges.head())
    print(n_points.head())
    print(n_nearest_points.head())
    print(n_edges.head())
    n_nodes = pd.concat([nodes, n_points, n_nearest_points], sort=True)

    print(n_nodes)

    return nodes, n_points, n_nearest_points, edges, n_edges


# connect the buildings to the graph
building_midpoints = gpd.GeoDataFrame(footprints.geometry.centroid, columns=['geometry'])
building_midpoints['x'] = building_midpoints.apply(lambda x: x.geometry.x, 1)
building_midpoints['y'] = building_midpoints.apply(lambda x: x.geometry.y, 1)
building_midpoints = building_midpoints[['x', 'y', 'geometry']]

nodes, n_points, n_nearest_points, edges, n_edges = connect_points_to_network(graph, building_midpoints)

fig, ax = plt.subplots()
n_points.plot(ax=ax, color='g')
n_nearest_points.plot(ax=ax, color='r')
edges.plot(ax=ax)
n_edges.plot(ax=ax)
footprints.plot(ax=ax, alpha=.3)
plt.show()

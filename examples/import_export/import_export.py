import pandas as pd
import networkx as nx
from district_heating_simulation import (input_output, projection)

edge_list = pd.read_csv('data/edge_list.csv', header=0, index_col='pipe_no')
node_list = pd.read_csv('data/node_list.csv')
heating_network = input_output.create_network(edge_list, node_list)

# reproject graph
heating_network.graph = {'crs': {'init': 'epsg:4326'}, 'name': 'example_dhn'}
to_crs = {'datum': 'WGS84',
          'ellps': 'WGS84',
          'proj' : 'utm',
          'zone' : 35,
          'units': 'm'}

G_proj = projection.project_graph(heating_network, to_crs=to_crs)
node_gdf, edge_gdf = input_output.graph_to_gdfs(G_proj)

# export to geodataframe
filename_export = 'example_dhn'
filename_nodes = r"%s_nodes.shp" % filename_export
filename_edges = r"%s_edges.shp" % filename_export

invalid_cols = []
for col in invalid_cols:
    edge_gdf[col] = edge_gdf[col].astype(str)
node_gdf.to_file(filename_nodes)
edge_gdf.to_file(filename_edges)

# export to edgelist/nodelist
edge_list = input_output.to_edge_list(heating_network)
node_list = input_output.to_node_list(heating_network)
edge_list.to_csv('example_dhn_edgelist.csv')
node_list.to_csv('example_dhn_nodelist.csv')
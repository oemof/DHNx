import pandas as pd
import networkx as nx
from district_heating_simulation import (input_output, projection)

edge_list = pd.read_csv('data/edge_list.csv', header=0, index_col='pipe_no')
node_list = pd.read_csv('data/node_list.csv')
G = input_output.create_network(edge_list, node_list)

G.graph = {'crs': {'init': 'epsg:4326'}, 'name': 'fictious_dhn'}
to_crs = {'datum': 'WGS84',
          'ellps': 'WGS84',
          'proj' : 'utm',
          'zone' : 35,
          'units': 'm'}

G_proj = projection.project_graph(G, to_crs=to_crs)

node_gdf, edge_gdf = input_output.graph_to_gdfs(G_proj)

place_name_out = 'fictios_dhn'
nodes_out = r"shapefiles/%s_nodes.shp" % place_name_out
edges_out = r"shapefiles/%s_edges.shp" % place_name_out

invalid_cols = []
for col in invalid_cols:
    edge_gdf[col] = edge_gdf[col].astype(str)
node_gdf.to_file(edges_out)
edge_gdf.to_file(nodes_out)

def to_edge_list(G):
    edge_list = nx.to_pandas_edgelist(G, source='from_node', target='to_node')
    edge_list = edge_list[['from_node', 'to_node', 'lenght_m', 'diameter_mm', 'heat_transfer_coefficient_W/mK', 'roughness_mm']]
    edge_list.index.name = 'pipe_no'
    
    return edge_list

edge_list = to_edge_list(G)
edge_list.to_csv('write_edgelist.csv')

def to_node_list(G):
    nodelist = G.nodes(data=True)
    nodes = [n for n, d in nodelist]
    all_keys = set().union(*(d.keys() for n, d in nodelist))
    node_attr = {k: [d.get(k, float("nan")) for n, d in nodelist] for k in all_keys}
    nodelistdict = {'node_id': nodes}
    nodelistdict.update(node_attr)
    node_list = pd.DataFrame(nodelistdict)
    node_list = node_list.set_index('node_id')
    node_list = node_list[['lat', 'lon', 'node_type']]
    
    return node_list

node_list = to_node_list(G)
node_list.to_csv('write_nodelist.csv')
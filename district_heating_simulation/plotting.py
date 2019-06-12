import networkx as nx
from math import sqrt
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import pandas as pd
import numpy as np

def draw_network(G, node_sizes, node_colors, edge_colors, edge_width, figsize):
    # pos = nx.circular_layout(G)
    # pos = nx.spring_layout(G)
    # pos = nx.fruchterman_reingold_layout(G.to_undirected())
    pos = {node_id: np.array([data['lon'], data['lat']]) for node_id, data in G.nodes(data=True)}
    fig = plt.figure(figsize=figsize)
    nodes = nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors)
    labels = nx.draw_networkx_labels(G, pos, font_color='w')
    edges = nx.draw_networkx_edges(G, pos, node_size=node_sizes, arrowstyle='->',
                                   arrowsize=10, edge_color=edge_colors,
                                   edge_cmap=plt.cm.hot, width=edge_width)


    ax = plt.gca()
    ax.set_axis_off()
    plt.show()




def draw_G(G, fig_width, fig_height, bgcolor='w',
               use_geom=False, edge_color='b', edge_linewidth=1,
               edge_alpha=1, node_size=3, node_color='r', node_alpha=1,
               node_edgecolor='r', node_zorder=1):

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor=bgcolor)
    lines = []
    for u, v, data in G.edges(data=True):
        if 'geometry' in data and use_geom:
            # if it has a geometry attribute (a list of line segments), add them
            # to the list of lines to plot
            xs, ys = data['geometry'].xy
            lines.append(list(zip(xs, ys)))
        else:
            # if it doesn't have a geometry attribute, the edge is a straight
            # line from node to node
            x1 = G.nodes[u]['lon']
            y1 = G.nodes[u]['lat']
            x2 = G.nodes[v]['lon']
            y2 = G.nodes[v]['lat']
            line = [(x1, y1), (x2, y2)]
            lines.append(line)

    # add the lines to the axis as a linecollection
    lc = collections.LineCollection(lines, colors=edge_color, linewidths=edge_linewidth, alpha=edge_alpha, zorder=2)
    ax.add_collection(lc)

    node_Xs = [float(x) for _, x in G.nodes(data='lon')]
    node_Ys = [float(y) for _, y in G.nodes(data='lat')]
    ax.scatter(node_Xs, node_Ys, s=node_size, c=node_color, alpha=node_alpha, edgecolor=node_edgecolor, zorder=node_zorder)

    plt.show()
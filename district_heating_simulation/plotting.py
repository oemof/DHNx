import networkx as nx
import osmnx as ox
import folium as fol
from folium.features import DivIcon
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import pandas as pd
import numpy as np
from math import sqrt


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


def make_plot(data, place, point, distance=1000, dpi=300,
              network_type='drive', bldg_color='#ABABAB',
              street_widths=None, default_width=0.75):
    """
    Create a plot of the given coordinates with buildings & streets

    Parameters
    ----------
    data: pandas df
        the data which will be plotted
    place : string
        name of the place/figure
    point : tuple
        the center point as coordinates
    distance : numeric
        how many meters to extend north, south, east, and west from the center
        point
    dpi : int
        the resolution of the image file
    network_type : string
        what type of network to get
    bldg_color : string
        the color of the buildings
    street_widths : dict
        where keys are street types and values are widths to plot in pixels
        (https://wiki.openstreetmap.org/wiki/Key:highway)
    default_width : numeric
        the default street width in pixels for any street type not found in
        street_widths dict

    Returns
    -------
    None
    """
    # osmnx config
    ox.config(use_cache=False, log_console=True)

    # add color column in data
    color = {'producer': '#ff0000', 'consumer': '#00ff00', 'split': '#000000'}
    data = (data.assign(node_color=data['node_type'])
                .replace({'node_color': color}))

    # get GeoDataFrame
    gdf = ox.footprints.footprints_from_point(point=point, distance=distance)

    # plot a figure-ground diagram of a street network
    fig, ax = ox.plot_figure_ground(point=point, dist=distance, dpi=dpi,
                                    bgcolor='#333333', edge_color='w',
                                    network_type=network_type,
                                    street_widths=street_widths,
                                    default_width=default_width,
                                    fig_length=20, save=False, show=False,
                                    close=False)

    # plot a GeoDataFrame of footprints
    fig, ax = ox.footprints.plot_footprints(gdf, fig=fig, ax=ax, dpi=dpi,
                                            color=bldg_color, figsize=(20, 20),
                                            set_bounds=False, save=False,
                                            show=False, close=False)

    # add points depending on data (x=longitude, y=latitude)
    ax.scatter(data['lon'].tolist(), data['lat'].tolist(),
               c=data['node_color'].tolist(), s=500)

    # add labels 
    for i in range(0, len(data)):
        ax.annotate(data['node_id'][i], xy=(data['lon'][i], data['lat'][i]),
                    color='blue', size=16, fontweight=1000)

    # save figure
    plt.savefig('plot_'+place+'.png', dpi=dpi, facecolor='#333333')
    print('Figure saved as '+place+'.png')


def create_interactive_map(data, map_name):
    # get average coordinates
    avg_lat = data['lat'].mean()
    avg_lon = data['lon'].mean()

    # add color column
    color = {'producer': '#ff0000', 'consumer': '#00ff00', 'split': '#000000'}
    data = (data.assign(node_color=data['node_type'])
                .replace({'node_color': color}))

    # create map
    m = fol.Map(location=[avg_lat, avg_lon], zoom_start=8)

    for i in range(0, len(data)):
        # draw colorful circles
        fol.CircleMarker([data['lat'][i], data['lon'][i]],
                         radius=20,
                         # popup=data['node_id'][i],
                         color=data['node_color'][i],
                         fill_color=data['node_color'][i]).add_to(m)

        # draw node ids
        fol.Marker([data['lat'][i], data['lon'][i]],
                   icon=DivIcon(icon_size=(20, 30),
                                icon_anchor=(0, 0),
                                html='<div style="font-size: 16pt">%s</div>'
                                % data['node_id'][i])).add_to(m)

    # save map
    m.save(map_name+'.html')

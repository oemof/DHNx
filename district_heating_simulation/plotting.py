import networkx as nx
import osmnx as ox
import folium as fol
from folium.features import DivIcon
import matplotlib.pyplot as plt
import matplotlib.collections as collections
from matplotlib.lines import Line2D
import pandas as pd
import numpy as np
from math import sqrt


class Network:
    """
    Create Network object

    Attributes
    ----------
    place : string
        name of the place/figure
    point : tuple
        the center point as coordinates
    node_data: pandas df
        the data which will be used as coordinates of nodes
    edge_data: pandas df
        the data which will be used as connections of nodes

    """
    def __init__(self, name, point, node_data, edge_data, **kwargs):
        self.name = name
        self.point = point
        self.node_data = node_data
        self.edge_data = edge_data
        self.node_id = node_data['node_id']
        self.lat = node_data['lat']
        self.lon = node_data['lon']
        self.node_type = node_data['node_type']
        self._add_colors()


    def _add_colors(self):
        color = {'producer': '#ff0000',
                 'consumer': '#00ff00',
                 'split': '#000000'}
        
        self.node_data = (self.node_data
                              .assign(node_color=self.node_data['node_type'])
                              .replace({'node_color': color}))

        return self.node_data['node_color']


    def _get_sw(self):
        sw = {'motorway': 3.0,
              'trunk': 2.5,
              'primary': 1.5,
              'secondary': 1.0,
              'tertiary': 1.0,
              'unclassified': 0.75,
              'residential': 0.75}

        return sw


    def _add_points(self, ax):
        ax.scatter(self.lon.tolist(),
                   self.lat.tolist(),
                   c=self.node_data['node_color'].tolist(),
                   s=500)


    def _add_labels(self, ax):
        for i in range(0, len(self.node_data)):
            ax.annotate(self.node_data['node_id'][i],
                        xy=(self.lon[i], self.lat[i]),
                        color='blue',
                        size=16,
                        fontweight=1000)


    def _draw_edges(self, ax):
        for i in range(0, len(self.edge_data)):
            edge = [(self.lon[self.edge_data['node_id_1'][i]],
                     self.lat[self.edge_data['node_id_1'][i]]),
                    (self.lon[self.edge_data['node_id_2'][i]],
                     self.lat[self.edge_data['node_id_2'][i]])]
            (edge_lon, edge_lat) = zip(*edge)

            # linewidth settings
            lw_avg = self.edge_data['value'].mean()
            lw = self.edge_data['value'][i] / lw_avg

            # add_lines
            if self.edge_data['edge_type'][i] == 'elec':
                ax.add_line(Line2D(edge_lon, edge_lat,
                                   linewidth=lw*3,
                                   color='blue'))
            else:
                ax.add_line(Line2D(edge_lon, edge_lat,
                   linewidth=lw*3,
                   color='orange'))


    def draw_map(self, distance, dpi):
        sw = self._get_sw()

        # osmnx config
        ox.config(use_cache=False, log_console=False)

        # get GeoDataFrame
        gdf = ox.footprints.footprints_from_point(point=self.point,
                                                  distance=distance)

        # plot a figure-ground diagram of a street network
        fig, ax = ox.plot_figure_ground(point=self.point,
                                        dist=distance,
                                        street_widths=sw,
                                        dpi=dpi,
                                        bgcolor='#333333',
                                        edge_color='w',
                                        network_type='drive',  
                                        default_width=0.75,
                                        fig_length=20,
                                        save=False,
                                        show=False,
                                        close=False)

        # plot a GeoDataFrame of footprints
        fig, ax = ox.footprints.plot_footprints(gdf, fig=fig, ax=ax,
                                                dpi=dpi,
                                                color='#ABABAB',
                                                figsize=(20, 20),
                                                set_bounds=False,
                                                save=False,
                                                show=False,
                                                close=False)

        # add points
        self._add_points(ax)

        # add labels
        self._add_labels(ax)

        # draw edges
        self._draw_edges(ax)

        return plt


    def create_interactive_map(self):
        # create map
        m = fol.Map(location=[self.lat.mean(), self.lon.mean()],
                    zoom_start=14)

        for i in range(0, len(self.node_data)):
            # draw nodes
            fol.CircleMarker([self.lat[i], self.lon[i]],
                             # popup=data['node_id'][i],
                             color=self.node_data['node_color'][i],
                             fill_color=self.node_data['node_color'][i],
                             radius=20).add_to(m)

            # draw node ids
            fol.Marker([self.lat[i], self.lon[i]],
                       icon=DivIcon(icon_size=(-35, 75),
                       icon_anchor=(0, 0),
                       html='<div style="font-size: 16pt">%s</div>'
                       % self.node_data['node_id'][i])).add_to(m)

        for i in range(0, len(self.edge_data)):
            # linewidth settings
            lw_avg = self.edge_data['value'].mean()
            lw = self.edge_data['value'][i] / lw_avg

            # draw edges
            if self.edge_data['edge_type'][i] == 'elec':
                fol.PolyLine(locations=[[self.lat[self.edge_data['node_id_1'][i]],
                                         self.lon[self.edge_data['node_id_1'][i]]],
                                        [self.lat[self.edge_data['node_id_2'][i]],
                                         self.lon[self.edge_data['node_id_2'][i]]]],
                             color='blue',
                             weight=lw*3).add_to(m)
            else:
                fol.PolyLine(locations=[[self.lat[self.edge_data['node_id_1'][i]],
                                         self.lon[self.edge_data['node_id_1'][i]]],
                                        [self.lat[self.edge_data['node_id_2'][i]],
                                         self.lon[self.edge_data['node_id_2'][i]]]],
                             color='orange',
                             weight=lw*3).add_to(m)
        return m


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

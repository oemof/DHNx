import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.collections as collections
from cartopy.io.img_tiles import GoogleTiles

class InteractiveMap():
    r"""


    """
    def __init__(self, thermal_network):
        pass

    def draw(self):
        pass


class StaticMap():
    r"""


    """
    def __init__(self, thermal_network):
        pass

    def draw(self):
        pass


class GraphPlot():
    r"""


    """
    def __init__(self, thermal_network, figsize=(5,5), node_size=3,
                 edge_width=3, node_color='r', edge_color='g'):

        self.graph = thermal_network.get_nx_graph()
        self.figsize = figsize
        self.node_size = node_size
        self.edge_width = edge_width
        self.node_color = node_color
        self.edge_color = edge_color
        self.positions = {node_id: np.array([data['lon'], data['lat']])
                          for node_id, data in self.graph.nodes(data=True)}
        self.extent = self.get_extent()
        print(self.extent)

    def get_extent(self):
        lon = [pos[0] for pos in self.positions.values()]
        lat = [pos[1] for pos in self.positions.values()]
        return  np.min(lon), np.max(lon), np.min(lat), np.max(lat)

    def draw(self, no_axis=False):
        fig = plt.figure(figsize=self.figsize)
        nodes = nx.draw_networkx_nodes(self.graph,
                                       self.positions,
                                       node_size=self.node_size,
                                       node_color=self.node_color)

        labels = nx.draw_networkx_labels(self.graph,
                                         self.positions,
                                         font_color='w')

        edges = nx.draw_networkx_edges(self.graph,
                                       self.positions,
                                       node_size=self.node_size,
                                       arrowstyle='->',
                                       arrowsize=10,
                                       edge_color=self.edge_color,
                                       edge_cmap=plt.cm.hot,
                                       width=self.edge_width)

        if no_axis:
            ax = plt.gca()
            ax.set_axis_off()

        return plt

    def draw_G(self, bgcolor='w', no_axis=False, background_map=False,
               use_geom=False, edge_color='b', edge_linewidth=1,
               edge_alpha=1, node_size=3, node_color='r', node_alpha=1,
               node_edgecolor='r', node_zorder=1):

        G = self.graph

        if background_map:
            imagery = GoogleTiles()
            zoom_level = 7
            fig, ax = plt.subplots(figsize=self.figsize,
                                   facecolor=bgcolor,
                                   subplot_kw={'projection': imagery.crs})
            ax.set_extent(self.extent, crs=imagery.crs)
            ax.add_image(imagery, zoom_level)
            ax.plot(12, 52, marker='o', color='red', markersize=12,
                    alpha=0.7)
        else:
            fig, ax = plt.subplots(figsize=self.figsize, facecolor=bgcolor)

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
        lc = collections.LineCollection(lines,
                                        colors=edge_color,
                                        linewidths=edge_linewidth,
                                        alpha=edge_alpha,
                                        zorder=2)
        ax.add_collection(lc)

        node_Xs = [float(x) for _, x in G.nodes(data='lon')]
        node_Ys = [float(y) for _, y in G.nodes(data='lat')]

        ax.scatter(node_Xs,
                   node_Ys,
                   s=node_size,
                   c=node_color,
                   alpha=node_alpha,
                   edgecolor=node_edgecolor,
                   zorder=node_zorder)

        if no_axis:
            ax = plt.gca()
            ax.set_axis_off()

        return plt

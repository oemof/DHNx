import folium as fol
from folium.features import DivIcon
from collections import namedtuple
from cartopy.io.img_tiles import Stamen
from cartopy import crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.collections as collections
import numpy as np


class InteractiveMap():
    r"""


    """
    def __init__(self, thermal_network, **kwargs):
        self.node_data = thermal_network.nodes
        self.edge_data = thermal_network.edges
        self.edge_data['value'] = 1
        self.node_id = self.node_data.index
        self.lat = self.node_data['lat']
        self.lon = self.node_data['lon']
        self.node_type = self.node_data['node_type']
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

    def _get_bearing(self, p1, p2):
        '''
        Returns compass bearing from p1 to p2

        Parameters
        p1 : namedtuple with lat lon
        p2 : namedtuple with lat lon

        Return
        compass bearing of type float
        '''
        long_diff = np.radians(p2.lon - p1.lon)

        lat1 = np.radians(p1.lat)
        lat2 = np.radians(p2.lat)

        x = np.sin(long_diff) * np.cos(lat2)
        y = (np.cos(lat1) * np.sin(lat2) 
            - (np.sin(lat1) * np.cos(lat2) 
            * np.cos(long_diff)))

        bearing = np.degrees(np.arctan2(x, y))

        # adjusting for compass bearing
        if bearing < 0:
            return bearing + 360

        return bearing

    def _get_arrows(self, locations, color='black', size=8, n_arrows=3):
        '''
        Get a list of correctly placed and rotated 
        arrows/markers to be plotted

        Parameters
        locations : list of lists of lat lons that represent the 
                    start and end of the line. 
                    eg [[41.1132, -96.1993],[41.3810, -95.8021]]
        color : default is 'black'
        size : default is 8
        n_arrows : number of arrows to create.  default is 3

        Return
        list of arrows/markers
        '''

        Point = namedtuple('Point', field_names=['lat', 'lon'])

        # creating point from our Point named tuple
        p1 = Point(locations[0][0], locations[0][1])
        p2 = Point(locations[1][0], locations[1][1])

        # getting the rotation needed for our marker.  
        # Subtracting 90 to account for the marker's orientation
        # of due East(get_bearing returns North)
        rotation = self._get_bearing(p1, p2) - 90

        # get an evenly space list of lats and lons for our arrows
        # note that I'm discarding the first and last for aesthetics
        # as I'm using markers to denote the start and end
        arrow_lats = np.linspace(p1.lat, p2.lat, n_arrows + 2)[1:n_arrows+1]
        arrow_lons = np.linspace(p1.lon, p2.lon, n_arrows + 2)[1:n_arrows+1]

        arrows = []

        #creating each "arrow" and appending them to our arrows list
        for points in zip(arrow_lats, arrow_lons):
            arrows.append(fol.RegularPolygonMarker(location=points,
                          color=color, number_of_sides=3,
                          radius=size, rotation=rotation, fill=True))

        return arrows

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
                       % self.node_data.index[i])).add_to(m)

        for i in range(0, len(self.edge_data)):
            # linewidth settings
            lw_avg = self.edge_data['value'].mean()
            lw = self.edge_data['value'][i] / lw_avg

            fol.PolyLine(locations=[[self.lat[self.edge_data['from_node'][i]],
                                     self.lon[self.edge_data['from_node'][i]]],
                                    [self.lat[self.edge_data['to_node'][i]],
                                     self.lon[self.edge_data['to_node'][i]]]],
                         color='orange',
                         weight=lw*3).add_to(m)

            arrows = self._get_arrows(
                locations=[[self.lat[self.edge_data['from_node'][i]],
                            self.lon[self.edge_data['from_node'][i]]],
                           [self.lat[self.edge_data['to_node'][i]],
                            self.lon[self.edge_data['to_node'][i]]]],
                color='orange', n_arrows=3)

            for arrow in arrows:
                arrow.add_to(m)

        return m


class StaticMap():
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
        self.extent = self._get_extent()
        pass

    def _get_extent(self):
        lon = [pos[0] for pos in self.positions.values()]
        lat = [pos[1] for pos in self.positions.values()]
        extent = np.array([np.min(lon), np.max(lon), np.min(lat), np.max(lat)])
        delta = [extent[1] - extent[0], extent[3] - extent[2]]
        extent += 0.1 * np.array([-delta[0], delta[0], -delta[1], delta[1]])
        return extent

    def draw(self, bgcolor='w', no_axis=False, background_map=False,
               use_geom=False, edge_color='b', edge_linewidth=2,
               edge_alpha=1, node_size=40, node_color='r', node_alpha=1,
               node_edgecolor='r', node_zorder=1):
        """
        This function has been adapted from osmnx plots.plot_graph() function.
        """
        if background_map:
            imagery = Stamen(style='toner-lite')
            zoom_level = 15
            fig, ax = plt.subplots(figsize=self.figsize,
                                   subplot_kw={'projection': imagery.crs})
            ax.set_extent(self.extent, crs=ccrs.Geodetic())
            ax.add_image(imagery, zoom_level, alpha=1, interpolation='bilinear')

        else:
            fig, ax = plt.subplots(figsize=self.figsize, facecolor=bgcolor,
                                   subplot_kw = {'projection': ccrs.Mercator()})
            ax.set_extent(self.extent, crs=ccrs.Geodetic())

        lines = []
        for u, v, data in self.graph.edges(data=True):
            if 'geometry' in data and use_geom:
                # if it has a geometry attribute (a list of line segments), add them
                # to the list of lines to plot
                xs, ys = data['geometry'].xy
                lines.append(list(zip(xs, ys)))
            else:
                # if it doesn't have a geometry attribute, the edge is a straight
                # line from node to node
                x1 = self.graph.nodes[u]['lon']
                y1 = self.graph.nodes[u]['lat']
                x2 = self.graph.nodes[v]['lon']
                y2 = self.graph.nodes[v]['lat']
                line = [(x1, y1), (x2, y2)]
                lines.append(line)

        # add the lines to the axis as a linecollection
        lc = collections.LineCollection(lines,
                                        colors=edge_color,
                                        linewidths=edge_linewidth,
                                        alpha=edge_alpha,
                                        zorder=2,
                                        transform=ccrs.Geodetic())
        ax.add_collection(lc)

        node_Xs = [float(x) for _, x in self.graph.nodes(data='lon')]
        node_Ys = [float(y) for _, y in self.graph.nodes(data='lat')]

        ax.scatter(node_Xs,
                   node_Ys,
                   s=node_size,
                   c=node_color,
                   alpha=node_alpha,
                   edgecolor=node_edgecolor,
                   zorder=node_zorder,
                   transform=ccrs.Geodetic())

        if no_axis:
            ax = plt.gca()
            ax.set_axis_off()

        return plt

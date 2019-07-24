"""
cmap: https://matplotlib.org/examples/color/colormaps_reference.html
osm: https://wiki.openstreetmap.org/wiki/Tile_servers

The original package of contextily does not support caching but there are
several approaches pending. Use the following version until caching is
officially supported:

pip install git+https://github.com/uvchik/contextily.git
"""

import os
import geopandas as gpd
from matplotlib import pyplot as plt
import contextily as ctx
from matplotlib.lines import Line2D
from matplotlib import cm


def add_basemap(ax, zoom, path=None, alpha=1.0,
                url='https://c.tile.openstreetmap.org'):
    url = '/'.join(s.strip('/') for s in [url, '/{z}/{x}/{y}.png'])
    xmin, xmax, ymin, ymax = ax.axis()
    try:
        basemap, extent = ctx.bounds2img(xmin, ymin, xmax, ymax, zoom=zoom,
                                         url=url, cache_dir=path)
    except TypeError:
        basemap, extent = ctx.bounds2img(xmin, ymin, xmax, ymax, zoom=zoom,
                                         url=url)
    ax.imshow(basemap, extent=extent, interpolation='bilinear', alpha=alpha)
    # restore original x/y limits
    ax.axis((xmin, xmax, ymin, ymax))


def building_plot(url, zoom, cmap, bg_alpha, plot_streets=False,
                  show_plot=True):
    """
    Parameters
    ----------
    url : str
        The url of the tile server. See the osm wiki for examples:
        https://wiki.openstreetmap.org/wiki/Tile_servers
    zoom : int
        OSM map zoom level.
    cmap : str or matplotlib.colors.Colormap
        Name of a matplotlib colormap or a colormap instance.
    bg_alpha : float
        Alpha value for the background map.
    plot_streets : bool
        Plot the streets as lines. Default=False.

    """
    geopath = os.path.join(os.path.dirname(__file__), 'geometries')

    ax = plt.figure(figsize=(5, 6)).add_subplot(1, 1, 1)

    buildings = gpd.read_file(os.path.join(geopath, 'heide_buildings.geojson'))
    if plot_streets:
        streets = gpd.read_file(os.path.join(geopath, 'heide_streets.geojson'))
    else:
        streets = None

    cat_values = sorted(buildings['Zone'].unique())
    cat_number = len(cat_values)

    if isinstance(cmap, str):
        cmap = cm.get_cmap(cmap, cat_number)

    ax = buildings.to_crs(epsg=3857).plot(column='Zone', cmap=cmap, ax=ax)
    if plot_streets:
        streets.to_crs(epsg=3857).plot(ax=ax)
    add_basemap(ax, zoom=zoom, path=cache_path, alpha=bg_alpha,
                url=url)
    ax.set_axis_off()

    v = 0
    labels = []
    custom_lines = []
    for n in range(cat_number):
        custom_lines.append(Line2D([0], [0], color=cmap(v), lw=4))
        v = v + 1/cat_number
        labels.append(cat_values[n])

    ax.legend(custom_lines, labels)
    plt.subplots_adjust(left=0, bottom=0, right=1, top=1)

    fn = os.path.join(os.path.expanduser('~'), 'heide')
    # plt.savefig(fn + '.svg')
    plt.savefig(fn + '.png')
    print("Plot saved to {0}".format(fn + '.png'))
    if show_plot:
        plt.show()


if __name__ == "__main__":
    osm_maps = {
        'OSM default': 'https://a.tile.openstreetmap.org/',
        'Wikimedia Maps': 'https://maps.wikimedia.org/osm-intl/',
        'OpenCycleMap': 'http://tile.thunderforest.com/cycle/',
        'Humanitarian map style': 'http://a.tile.openstreetmap.fr/hot/',
        'OSM France': 'http://a.tile.openstreetmap.fr/osmfr/',
        'wmflabs_hike_bike': 'https://tiles.wmflabs.org/hikebike/',
        'wmflabs Hillshading': 'http://tiles.wmflabs.org/hillshading/',
        'wmflabs OSM BW': 'https://tiles.wmflabs.org/bw-mapnik/',
        'wmflabs OSM no labels': 'https://tiles.wmflabs.org/osm-no-labels/',
        'Stamen Toner': 'http://a.tile.stamen.com/toner/',
        'Stamen Watercolor': 'http://c.tile.stamen.com/watercolor/',
        'Thunderforest Landscape': 'http://tile.thunderforest.com/landscape/',
        'Thunderforest Outdoors': 'http://tile.thunderforest.com/outdoors/',
        'OpenTopoMap': 'https://a.tile.opentopomap.org/'
    }

    # ******** INPUTS
    cache_path = os.path.join(os.path.expanduser('~'), '.basemap_tiles')
    osm_url = osm_maps['wmflabs OSM BW']
    color_map = 'tab10'
    map_zoom = 17
    map_alpha = 0.7
    heide_streets = False
    show_plot = True
    # ******** INPUTS

    building_plot(osm_url, map_zoom, color_map, map_alpha, heide_streets,
                  show_plot)

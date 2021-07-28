# import matplotlib.pyplot as plt

from dhnx.input_output import OSMNetworkImporter
from dhnx.plotting import StaticMap
from dhnx.network import ThermalNetwork

place = (52.43034, 13.53806)

distance = 300

tnw = ThermalNetwork()

io = OSMNetworkImporter(tnw, place, distance)

io.load()

print(tnw)

# plot static map
static_map = StaticMap(tnw)

static_map.draw(background_map=False)

# plt.savefig('static_map_wo_background.png')

# tnw.to_csv_folder('osm_network')

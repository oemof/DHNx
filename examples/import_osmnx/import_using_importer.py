import dhnx
import matplotlib.pyplot as plt

tnw = dhnx.network.ThermalNetwork()
io = dhnx.input_output.OSMNetworkImporter(tnw, 0, 0)

io.load()

print(tnw)

# plot static map
static_map = dhnx.plotting.StaticMap(tnw)

static_map.draw(background_map=False)
plt.savefig('static_map_wo_background.png')

tnw.to_csv_folder('osm_network')

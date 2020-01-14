import matplotlib.pyplot as plt
import district_heating_simulation as dhs


# Initialize thermal network
network = dhs.network.ThermalNetwork()
network = network.load_from_csv('investment_input')

# Draw network
static_map = dhs.plotting.StaticMap(network)
static_map.draw(background_map=False)
plt.show()

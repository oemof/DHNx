import matplotlib.pyplot as plt
import dhnx


# Initialize thermal network
network = dhnx.network.ThermalNetwork()
network = network.from_csv_folder('investment_input_2')

network.optimize_investment()

# Draw network
static_map = dhnx.plotting.StaticMap(network)
static_map.draw(background_map=False)
plt.show()

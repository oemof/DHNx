import matplotlib.pyplot as plt
import district_heating_simulation as dhs


# Initialize thermal network
network = dhs.network.ThermalNetwork()
network = network.load_from_csv('operation_network')

# Draw network
network_plot = dhs.plotting.GraphPlot(network)
network_plot.draw_G(background_map=False)
plt.show()

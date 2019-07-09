import district_heating_simulation as dhs
import matplotlib.pyplot as plt

# initialize a thermal network
thermal_network = dhs.network.ThermalNetwork()

# load data from csv
thermal_network.load_from_csv('single_loop/')

# plot
graph_plot = dhs.plotting.GraphPlot(thermal_network)
graph_plot.draw_G(background_map=False)
plt.show()

# define problem

# create simulation model

# solve the model

# plot results
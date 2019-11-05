import district_heating_simulation as dhs
import matplotlib.pyplot as plt

# initialize a thermal network
thermal_network = dhs.network.ThermalNetwork()

# load data from csv
thermal_network = thermal_network.load_from_csv('data_csv_input/')

# save thermal network to csv
thermal_network.save_to_csv('data_csv_output/')

# save thermal network to GeoDataFrame
# thermal_network.save_to_gdf('data_gdf/')

# get graph of thermal network
graph = thermal_network.get_nx_graph()

# plot the graph
graph_plot = dhs.plotting.GraphPlot(thermal_network)
# plot_1 = graph_plot.draw()
plot_2 = graph_plot.draw_G(background_map=False)
plt.show()

# # plot static map
# static_map = dhs.plotting.StaticMap(thermal_network)
#
# # plot interactive map
# interactive_map = dhs.plotting.InteractiveMap(thermal_network)
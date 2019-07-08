import district_heating_simulation as dhs

# initialize a thermal network
thermal_network = dhs.network.ThermalNetwork()

# load data from csv
thermal_network.load_from_csv('data/')

# save thermal network to csv
thermal_network.save_to_csv('data2/')

# save thermal network to GeoDataFrame
# thermal_network.save_to_gdf('data2/')

# get graph of thermal network
graph = thermal_network.get_nx_graph()

# plot the graph
dhs.plotting.draw_G(graph, 5, 5)



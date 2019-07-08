import district_heating_simulation as dhs
import district_heating_simulation.network as nx

# initialize a thermal network
thermal_network = dhs.network.ThermalNetwork()

# load data from csv
thermal_network.load_from_csv('data/')
print(thermal_network.producers)

# save thermal network to csv
thermal_network.save_to_csv('data2/')

# save thermal network to GeoDataFrame
# thermal_network.save_to_gdf('data2/')

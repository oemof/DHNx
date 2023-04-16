
"""
Using the aggregation function to aggregate a network to a super network

"""

from dhnx.network import ThermalNetwork
from dhnx.gistools.geometry_operations import aggregation
import geopandas as gpd
import matplotlib.pyplot as plt

# Part I: Create a new network out of components using aggregation(forks, pipes, consumers, producers)

# import the components
pipes = gpd.read_file('network_data/pipes.geojson')
forks = gpd.read_file('network_data/forks.geojson')
consumers = gpd.read_file('network_data/consumers.geojson')
producers = gpd.read_file('network_data/producers.geojson')

# a new dict with the components of the super network is created
super_network = aggregation(forks, pipes, consumers, producers)

# plot of the super network
_, ax = plt.subplots()
super_network['super_pipes'].plot(ax=ax, color='red')
super_network['super_producers'].plot(ax=ax, color='blue')
super_network['super_forks'].plot(ax=ax, color='grey')
plt.title('Geometry after aggregation of network')
plt.show()

# export as geojson
super_network['super_forks'].to_file('super_network/super_forks.geojson', driver='GeoJSON')
super_network['super_pipes'].to_file('super_network/super_pipes.geojson', driver='GeoJSON')

# Part II: Create a new network out an existing network using aggregate()
# save the imported components in a dict
tn_input = {
        'forks': forks,
        'consumers': consumers,
        'producers': producers,
        'pipes': pipes,
}
# initialize a ThermalNetwork
network = ThermalNetwork()

# add the pipes, forks, consumer, and producers to the ThermalNetwork
for k, v in tn_input.items():
    network.components[k] = v

# create a new dict in network with the components of the super network
network.aggregate()

# plot the supernetwork
_, ax = plt.subplots()
network.aggregatednetwork['super_pipes'].plot(ax=ax, color='red')
network.aggregatednetwork['super_producers'].plot(ax=ax, color='blue')
network.aggregatednetwork['super_forks'].plot(ax=ax, color='grey')
plt.title('Geometry after aggregation of network')
plt.show()

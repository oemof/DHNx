import os
import sys

import district_heating_simulation as dhs


currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(os.path.dirname(currentdir))
sys.path.append(parentdir)

# initialize a thermal network
thermal_network = dhs.network.ThermalNetwork()

# load data from csv
thermal_network.load_from_csv('berlin_data')

# create interactive map
map = dhs.plotting.InteractiveMap(thermal_network)
map = map.draw()

# save interactive map
map.save('berlin.html')


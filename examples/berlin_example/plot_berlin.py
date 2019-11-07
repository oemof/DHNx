import os
import sys

import pandas as pd

from district_heating_simulation import plotting


currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(os.path.dirname(currentdir))
sys.path.append(parentdir)

# read data
node_data = pd.read_csv('berlin_node_list.csv')
edge_data = pd.read_csv('berlin_edge_list.csv')

# name of the place
place = 'berlin'

# coordinates of the place
point = (node_data['lat'].mean(), node_data['lon'].mean())

# create interactive map
map = plotting.InteractiveMap(place, point, node_data, edge_data)
map = map.draw()

# save interactive map
map.save(place+'.html')
print('Map saved as '+place+'.html')

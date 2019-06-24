import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(os.path.dirname(currentdir))
sys.path.append(parentdir)
from district_heating_simulation import plotting
import pandas as pd


# read data
node_data = pd.read_csv('berlin_node_list.csv')
edge_data = pd.read_csv('berlin_edge_list.csv')

# name of the place
place = 'berlin'

# coordinates of the place
point = (node_data['lat'].mean(), node_data['lon'].mean())

# create network & plot
net = plotting.Network(place, point, node_data, edge_data)
plot = net.draw_map(distance=2500, dpi=70)

# save plot
plot.savefig('plot_'+place+'.png', dpi=70, facecolor='#333333')
print('Figure saved as '+place+'.png')

# create interactive map
map = net.create_interactive_map()

# save interactive map
map.save(place+'.html')
print('Map saved as '+place+'.html')

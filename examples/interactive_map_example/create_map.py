import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(os.path.dirname(currentdir))
sys.path.append(parentdir)
from district_heating_simulation import plotting
import pandas as pd


# read data
data = pd.read_csv('example_list.csv')

# choose map name
map_name = 'example_map'

# create interactive map
plotting.create_interactive_map(data, map_name)

import os
import sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(os.path.dirname(currentdir))
sys.path.append(parentdir)
from district_heating_simulation import plotting
import pandas as pd


# read data
data = pd.read_csv('berlin_node_list.csv')

# name of the place
place = 'berlin'

# coordinates of the place
point = (52.5163, 13.3788)

# street widths of the plot
sw = {'motorway': 3.0, 'trunk': 2.5, 'primary': 1.5, 'secondary': 1.0,
      'tertiary': 1.0, 'unclassified': 0.75, 'residential': 0.75}

# create plot
plotting.make_plot(data, place, point, distance=2500, dpi=300,
                   street_widths=sw)

import matplotlib.pyplot as plt
import os

import dhnx

# Initialize a thermal networks
thermal_network = dhnx.network.ThermalNetwork()

# Load data from csv
input_data_dir = 'tree'

thermal_network.from_csv_folder(input_data_dir)

# Create simulation model
thermal_network.simulate(results_dir='tree_results')

# Plot and save results
print('================================================================')
for k, v in thermal_network.results['simulation'].items():
    print(k)
    print('----------------------------------------------------------------')
    print(v, '\n')
    print('================================================================')

import matplotlib.pyplot as plt
import os

import dhnx

# Initialize 2 thermal networks
tree_network = dhnx.network.ThermalNetwork()

# Load data from csv
tree_network.from_csv_folder('tree/')

# Create simulation model
tree_network.simulate()

# Plot and save results
print('================================================================')
for k, v in tree_network.results.items():
    print(k)
    print('----------------------------------------------------------------')
    print(v, '\n')
    print('================================================================')

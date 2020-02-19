import matplotlib.pyplot as plt
import os

import dhnx

# Initialize 2 thermal networks
tree_network = dhnx.network.ThermalNetwork()
looped_network = dhnx.network.ThermalNetwork()

# Load data from csv
tree_network.from_csv_folder('tree/')
looped_network.from_csv_folder('single_loop/')

# Plot
tree_graph_plot = dhnx.plotting.StaticMap(tree_network)
tree_graph_plot.draw(background_map=False)

looped_graph_plot = dhnx.plotting.StaticMap(looped_network)
looped_graph_plot.draw(background_map=False)
plt.show()

# Create simulation model
tree_network.simulate()
looped_network.simulate()

if not os.path.exists('results'):
    os.mkdir('results')

# Plot and save results
print('================================================================')
for k, v in tree_network.results.items():
    print(k)
    print('----------------------------------------------------------------')
    print(v, '\n')
    print('================================================================')
    v.to_csv(f'results/{k}.csv')

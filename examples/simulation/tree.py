import matplotlib.pyplot as plt
import os

import dhnx

# Initialize thermal network
tnw = dhnx.network.ThermalNetwork()

# Load data from csv
tnw.from_csv_folder('tree/input')

# Plot
graph_plot = dhnx.plotting.StaticMap(tnw)
graph_plot.draw(background_map=False)
plt.savefig('tree.svg')

# Create simulation model
tnw.simulate()

if not os.path.exists('results'):
    os.mkdir('results')

# Plot and save results
print('================================================================')
for k, v in tnw.results.items():
    print(k)
    print('----------------------------------------------------------------')
    print(v, '\n')
    print('================================================================')
    v.to_csv(f'results/{k}.csv')

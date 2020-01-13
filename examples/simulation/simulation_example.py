import matplotlib.pyplot as plt
import pandas as pd
import os

import district_heating_simulation as dhs

# Initialize 2 thermal networks
tree_network = dhs.network.ThermalNetwork()
looped_network = dhs.network.ThermalNetwork()

# Load data from csv
tree_network.load_from_csv('tree/')
looped_network.load_from_csv('single_loop/')

# Plot
tree_graph_plot = dhs.plotting.StaticMap(tree_network)
tree_graph_plot.draw(background_map=False)

looped_graph_plot = dhs.plotting.StaticMap(looped_network)
looped_graph_plot.draw(background_map=False)
plt.show()

# Define problem
mass_flow = pd.read_csv('problem/mass_flow.csv', index_col='snapshot')
temperature_drop = pd.read_csv('problem/temperature_drop.csv', index_col='snapshot')

# Create simulation model
tree_model = dhs.simulation.SimulationModel(tree_network)
tree_model.set_problem(mass_flow, temperature_drop)

# Solve the model
results = tree_model.solve()

if not os.path.exists('results'):
    os.mkdir('results')

# Plot and save results
print('================================================================')
for k, v in results.items():
    print(k)
    print('----------------------------------------------------------------')
    print(v, '\n')
    print('================================================================')
    v.to_csv(f'results/{k}.csv')

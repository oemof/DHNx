"""
Discrete DN number examples.

This examples shows how to perform an optimisation with an investment
in discrete DN numbers.

Please see the `pipes.csv` in the invest_data/network.

For each of the DN numbers a separate row is given in the table.
"""
import matplotlib.pyplot as plt
import dhnx

# Initialize thermal network
network = dhnx.network.ThermalNetwork()
network = network.from_csv_folder('twn_data')

# Load investment parameter
invest_opt = dhnx.input_output.load_invest_options('invest_data')

# plot network
static_map = dhnx.plotting.StaticMap(network)
static_map.draw(background_map=False)
plt.title('Given network')
plt.scatter(network.components.consumers['lon'], network.components.consumers['lat'],
            color='tab:green', label='consumers', zorder=2.5, s=50)
plt.scatter(network.components.producers['lon'], network.components.producers['lat'],
            color='tab:red', label='producers', zorder=2.5, s=50)
plt.scatter(network.components.forks['lon'], network.components.forks['lat'],
            color='tab:grey', label='forks', zorder=2.5, s=50)
plt.text(-2, 32, 'P0', fontsize=14)
plt.legend()
plt.show()

# Execute investment optimization
network.optimize_investment(invest_options=invest_opt)

# ####### Postprocessing and Plotting ###########

# get results
results_edges = network.results.optimization['components']['pipes']
print(results_edges[['from_node', 'to_node', 'hp_type', 'capacity',
                     'direction', 'costs', 'losses']])

# print(results_edges[['invest_costs[€]']].sum())
print('Objective value: ', network.results.optimization['oemof_meta']['objective'])

# assign new ThermalNetwork with invested pipes
twn_results = network
twn_results.components['pipes'] = results_edges[results_edges['capacity'] > 0.001]

# plot invested edges
static_map_2 = dhnx.plotting.StaticMap(twn_results)
static_map_2.draw(background_map=False)
plt.title('Result network')
plt.scatter(network.components.consumers['lon'], network.components.consumers['lat'],
            color='tab:green', label='consumers', zorder=2.5, s=50)
plt.scatter(network.components.producers['lon'], network.components.producers['lat'],
            color='tab:red', label='producers', zorder=2.5, s=50)
plt.scatter(network.components.forks['lon'], network.components.forks['lat'],
            color='tab:grey', label='forks', zorder=2.5, s=50)
plt.text(-2, 32, 'P0', fontsize=14)
for r, c in twn_results.components['pipes'].iterrows():
    size = c["hp_type"]
    type = c["from_node"].split("-")[0]
    id = c["from_node"].split("-")[1]
    lat_0 = twn_results.components[type].loc[id].lat
    lon_0 = twn_results.components[type].loc[id].lon
    type = c["to_node"].split("-")[0]
    id = c["to_node"].split("-")[1]
    lat_1 = twn_results.components[type].loc[id].lat
    lon_1 = twn_results.components[type].loc[id].lon
    lat_mid = lat_0 + 0.5 * (lat_1 - lat_0)
    lon_mid = lon_0 + 0.5 * (lon_1 - lon_0)
    plt.text(lon_mid, lat_mid, size, va="center", ha="center")

plt.legend()
plt.show()

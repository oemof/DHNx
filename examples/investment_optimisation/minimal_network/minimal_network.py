import matplotlib.pyplot as plt
import dhnx


# Initialize thermal network
network = dhnx.network.ThermalNetwork()
network = network.from_csv_folder('twn_data')

# Load investment parameter
invest_opt = dhnx.input_output.load_invest_options('invest_data')

# Execute investment optimization
network.optimize_investment(invest_options=invest_opt,
                            settings={'write_lp_file': True})

# ####### Postprocessing and Plotting ###########
# Draw network
static_map = dhnx.plotting.StaticMap(network)
static_map.draw(background_map=False)
plt.title('Given network')
plt.show()

# get results
results_edges = network.results.optimization['components']['pipes']
print('*Results*')
print(results_edges)
print('')
print('Objective Value: ',
      network.results.optimization['oemof_meta']['objective'])

# manually recalculate total costs
total_costs = (33 * 3.162 + 15 * 1 + 18 * 1 + 18 * 0.5) * 0.5
print('Costs re-calculation: ', total_costs)

col_size = [x for x in list(results_edges.columns) if '.size' in x]
col_size = [x for x in col_size if x.split('.')[1] == 'size']

# get indices which are existing or invested
ind = results_edges[results_edges['capacity'] > 0].index

# select invested edges
network_result = network
network_result.components['pipes'] = results_edges.loc[ind]

# plot results network
static_map = dhnx.plotting.StaticMap(network_result)
static_map.draw(background_map=False)
plt.title('Optimization result')
plt.show()

import matplotlib.pyplot as plt
import dhnx

# Initialize thermal network
network = dhnx.network.ThermalNetwork()
network = network.from_csv_folder('network')

# general optimisation settings
set = {'num_ts': 3,
       'time_res': 1,
       'start_date': '1/1/2018',
       'frequence': 'H',
       'solver': 'cbc',
       'solve_kw': {'tee': True},
       'simultaneity': 0.8,
       'bidirectional_pipes': True,
       'print_logging_info': True,
       }

invest_opt = dhnx.input_output.load_invest_options('invest_options')

network.optimize_investment(**set, invest_options=invest_opt)

# Draw network
static_map = dhnx.plotting.StaticMap(network)
static_map.draw(background_map=False)
plt.title('Given network')
plt.show()

# get results
results_edges = network.results.optimization['components']['pipes']
print('*Results*')
print(results_edges)

# get indices which are existing or invested
ind = results_edges[results_edges['capacity'] > 0].index

edges = network.components['pipes']
ind_exist = list(edges[edges['existing'] == 1].index)

# plot existing network
network_exist = network
network_exist.components['pipes'] = edges.loc[ind_exist]

# plot existing network
static_map = dhnx.plotting.StaticMap(network_exist)
static_map.draw(background_map=False)
plt.title('Existing pipes')
plt.show()

# select xisting or invested edges
network_result = network
network_result.components['pipes'] = results_edges.loc[ind]

# plot results network
static_map = dhnx.plotting.StaticMap(network_result)
static_map.draw(background_map=False)
plt.title('Investment result')
plt.show()

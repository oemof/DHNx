import matplotlib.pyplot as plt
import pandas as pd
import dhnx


# Initialize thermal network
network = dhnx.network.ThermalNetwork()
network = network.from_csv_folder('twn_data')

# DHS pipeline invest data
df_pipes = pd.DataFrame(
    {
        "label_3": "your-pipe-type-label",
        "active": 1,
        "nonconvex": 1,
        "l_factor": 0.000002,
        "l_factor_fix": 0.001,
        "cap_max": 10000,
        "cap_min": 25,
        "capex_pipes": 5,
        "fix_costs": 200,
    }, index=[0],
)

# Load investment parameter
invest_opt = dhnx.input_output.load_invest_options('invest_data')

# Execute investment optimization
network.optimize_investment(
    pipeline_invest_options=df_pipes,
    additional_invest_options=invest_opt,
    write_lp_file=True,
    print_logging_info=True,
)

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

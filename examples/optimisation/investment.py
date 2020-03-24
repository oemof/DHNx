import matplotlib.pyplot as plt
import dhnx


# Initialize thermal network
network = dhnx.network.ThermalNetwork()
network = network.from_csv_folder('investment_input_2/network')

# general optimisation settings
num_ts = 2      # number of timesteps
time_res = 1    # time resolution: [1/h] (percentage of hour) => 0.25 is quarter-hour resolution
set = {'num_ts': num_ts,            # number of timesteps
       'time_res': time_res,         # time resolution: [1/h] (percentage of hour) => 0.25 is quarter-hour resolution
       'rate': 0.01,                 # interest rate (just in case of annuity)
       'f_invest': num_ts / (8760 / time_res),   # scaling factor for investment costs (just in case annuity is on)
       # 'f_invest': 1,
       'start_date': '1/1/2018',     # start of datetimeindex for oemof solph
       'frequence': 'H',             # time resolution
       'solver': 'cbc',              # solver
       'solve_kw': {'tee': True},    # solver kwargs
       }

invest_opt = dhnx.input_output.load_invest_options('investment_input_2/invest_options')

network.optimize_investment(settings=set, invest_options=invest_opt)

# Draw network
static_map = dhnx.plotting.StaticMap(network)
static_map.draw(background_map=False)
plt.show()

# get results
results_edges = network.results.optimization['components']['edges']
print('*Results*')
print(results_edges)

col_size = [x for x in list(results_edges.columns) if '.size' in x]
col_size = [x for x in col_size if x.split('.')[1] == 'size']

ind_invest_not_zero = results_edges[ results_edges[col_size[0]] > 0.001 ].index

network_result = network
network_result.components['edges'] = results_edges.loc[ind_invest_not_zero]

# Draw investment results
static_map = dhnx.plotting.StaticMap(network_result)
static_map.draw(background_map=False)
plt.show()

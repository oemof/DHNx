import matplotlib.pyplot as plt
import dhnx


# Initialize thermal network
network = dhnx.network.ThermalNetwork()
network = network.from_csv_folder('investment_input_2/network')

# general optimisation settings
num_ts = 3     # number of timesteps
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
       # optimization types
       'dhs': 'optional',        # parameter which defines type of optimization. ...
       # either the heat supply should be via dhs ('fix') (=> all active houses are connected), ...
       # or is part of the optimization ('optional').
       'simultaneity': 'global',   # 'global' or 'timeseries' => a single timestep optimization is performed
       'global_SF': 0.8,           # global simultaneity factor. is only applied, if simultaneity='global'
       'SF_timeseries': 1,         # scaling factor for heat demand timeseries
       'SF_1_timeseries': 0.8,     # scaling factor for the first element of the timeseries (bei geoordneter JDL)
       'precalc_consumer_connections': True,
       'bidirectional_pipes': True,       # specify whether the distribution lines (from fork to fork) should be bidiretional or not,
                                          # if 'False', then two pipes are build in each direaction, instead of 1 bidirectional pipe
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

# get indices which are existing or invested
ind = []
for hp in col_size:
       if len(list(results_edges[results_edges[hp] > 0.001].index)) > 0:
              ind = ind + list(results_edges[results_edges[hp] > 0.001].index)

ind_exist = list(results_edges[results_edges['existing'] == 1].index)

# plot existing network
network_exist = network
network_exist.components['edges'] = results_edges.loc[ind_exist]

# plot existing network
static_map = dhnx.plotting.StaticMap(network_exist)
static_map.draw(background_map=False)
plt.show()

ind = ind + ind_exist

# select xisting or invested edges
network_result = network
network_result.components['edges'] = results_edges.loc[ind]

# plot results network
static_map = dhnx.plotting.StaticMap(network_result)
static_map.draw(background_map=False)
plt.show()


# TESTING #########################

# results = network.results['optimization']['oemof']
#
# label = 'infrastructure_' + 'heat_' + 'heatpipe-milp' + '_' + 'producers-0-forks-0'
#
# flow = [x for x in results.keys()
#         if x[1] is not None
#         if x[0].label.__str__() == label]
#
# results[flow[0]]['sequences']


# # maybe slow approach with lambda function
# df[hp + '.' + 'dir-1'] = df['from_node'] + '-' + df['to_node']
# df[hp + '.' + 'size-1'] = df[hp + '.' + 'dir-1'].apply(
#   lambda x: get_invest_val(label_base + x))
# df[hp + '.' + 'dir-2'] = df['to_node'] + '-' + df['from_node']
# df[hp + '.' + 'size-2'] = df[hp + '.' + 'dir-2'].apply(
#   lambda x: get_invest_val(label_base + x))

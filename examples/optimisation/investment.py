import matplotlib.pyplot as plt
import dhnx
import pandas as pd

# Initialize thermal network
network = dhnx.network.ThermalNetwork()
network = network.from_csv_folder('investment_input_2/network')

# general optimisation settings
num_ts = 3     # number of timesteps
time_res = 1    # time resolution: [1/h] (percentage of hour) => 0.25 is quarter-hour resolution
set = {'num_ts': num_ts,           # number of timesteps
       'time_res': time_res,       # time resolution: [1/h] (percentage of hour) => 0.25 is
                                   # quarter-hour resolution
       'rate': 0.01,               # interest rate (just in case of annuity)
       'f_invest': num_ts / (8760 / time_res),   # scaling factor for investment costs (just in case
                                                 # annuity is on)
       'start_date': '1/1/2018',     # start of datetimeindex for oemof solph
       'frequence': 'H',             # time resolution
       'solver': 'cbc',              # solver
       'solve_kw': {'tee': True},    # solver kwargs
       # optimization types
       'heat_demand': 'optional',    # parameter which defines type of optimization. ...
       # either the heat supply should be via dhs ('fix') (=> all active houses are connected), ...
       # or is part of the optimization ('optional').
       'simultaneity': 0.8,         # global simultaneity factor. is only applied,
                                    # if simultaneity='global'
       'bidirectional_pipes': True,       # specify whether the distribution lines (from fork to
                                          # fork) should be bidiretional or not,
                                          # if 'False', then two pipes are build in each direaction,
                                          # instead of 1 bidirectional pipe
       # 'dump_path': 'investment_input_2/',
       'get_invest_results': True
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

# recalculate objective value
print('Objective: ', network.results['optimization']['oemof_meta']['objective'])

col_res = 'heatpipe-milp.size'
df_invest = results_edges[results_edges[col_res] > 0].copy()
df_invest['test_costs'] = (df_invest[col_res] * 0.00959 + 236) * df_invest['length[m]']
costs = df_invest['test_costs'].sum()

print('Re-calculated costs: ', costs)
print('')

# recalc heat loss
# Re-calc heat loss
results = network.results['optimization']['oemof']
hp = [
    x for x in results.keys()
    if x[1] is None
    if 'heatpipe' in x[0].label[2]
]
len(hp)
len(results_edges.index)

label_list = [x[0].label[3] for x in hp]
heat_loss_list = [results[x]['sequences']['heat_loss'][0].squeeze() for x in hp]
heat_loss_total = sum(heat_loss_list)

df_heat_loss = pd.DataFrame([label_list, heat_loss_list]).T
df_heat_loss.columns = ['label', 'heat_loss']

print('Heat loss nodes: ', df_heat_loss['heat_loss'].sum())
print('Heat loss recalc: ', results_edges['heat_loss[kW]'].sum())

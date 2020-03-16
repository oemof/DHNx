import matplotlib.pyplot as plt
import dhnx


# Initialize thermal network
network = dhnx.network.ThermalNetwork()
network = network.from_csv_folder('investment_input_2')

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

network.optimize_investment(settings=set)

# Draw network
static_map = dhnx.plotting.StaticMap(network)
static_map.draw(background_map=False)
plt.show()

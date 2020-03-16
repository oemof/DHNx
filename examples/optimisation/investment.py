import matplotlib.pyplot as plt
import dhnx


# Initialize thermal network
network = dhnx.network.ThermalNetwork()
network = network.from_csv_folder('investment_input_2')

# some data -> need to be moved somewhere else
num_ts = 2      # number of timesteps
time_res = 1    # time resolution: [1/h] (percentage of hour)
# => 0.25 is quarter-hour resolution
set = {'num_ts': num_ts,  # number of timesteps
      'time_res': time_res,
      'rate': 0.01,
      'f_invest': num_ts / (8760 / time_res),   # just in case annuity is on
      # 'f_invest': 1,
      'start_date': '1/1/2018',
      'frequence': 'H',
      'solver': 'cbc',
      'solve_kw': {'tee': True},
      }

network.optimize_investment(settings=set)

# Draw network
static_map = dhnx.plotting.StaticMap(network)
static_map.draw(background_map=False)
plt.show()

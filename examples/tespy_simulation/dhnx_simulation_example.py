import dhnx

import_dir = 'single_pipe_simulation_input'

nw = dhnx.network.ThermalNetwork(import_dir)

nw.simulate()

print(nw.results)

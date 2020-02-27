import dhnx

import_dir = 'simulation_input'

nw = dhnx.network.ThermalNetwork(import_dir)

nw.simulate()

print(nw.results)

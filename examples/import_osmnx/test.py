import dhnx

tnw = dhnx.network.ThermalNetwork()
io = dhnx.input_output.OSMNetworkImporter(tnw, 0, 0)

io.load()
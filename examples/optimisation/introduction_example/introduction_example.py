import matplotlib.pyplot as plt
import dhnx


# Initialize thermal network
network = dhnx.network.ThermalNetwork()
network = network.from_csv_folder('twn_data')

# Load investment parameter
invest_opt = dhnx.input_output.load_invest_options('invest_data')

# plot network
static_map = dhnx.plotting.StaticMap(network)
static_map.draw(background_map=False)
plt.title('Given network')
plt.scatter(network.components.consumers['lon'], network.components.consumers['lat'],
            color='tab:green', label='consumers', zorder=2.5, s=50)
plt.scatter(network.components.producers['lon'], network.components.producers['lat'],
            color='tab:red', label='producers', zorder=2.5, s=50)
plt.scatter(network.components.forks['lon'], network.components.forks['lat'],
            color='tab:grey', label='forks', zorder=2.5, s=50)
plt.text(-2, 32, 'P0', fontsize=14)
plt.text(82, 0, 'P1', fontsize=14)
plt.legend()
plt.show()
# plt.savefig('intro_opti_network.svg')

# Execute investment optimization
network.optimize_investment(invest_options=invest_opt)

# ####### Postprocessing and Plotting ###########

# get results
results_edges = network.results.optimization['components']['edges']
print('*Results*')
print(results_edges)

# col_size = [x for x in list(results_edges.columns) if '.size' in x]
# col_size = [x for x in col_size if x.split('.')[1] == 'size']
#
# # get indices which are existing or invested
# ind = []
# for hp in col_size:
#     if len(list(results_edges[results_edges[hp] > 0.001].index)) > 0:
#         ind = ind + list(results_edges[results_edges[hp] > 0.001].index)
#
# # select invested edges
# network_result = network
# network_result.components['edges'] = results_edges.loc[ind]
#
# # plot results network
# static_map = dhnx.plotting.StaticMap(network_result)
# static_map.draw(background_map=False)
# plt.title('Optimization result')
# plt.show()

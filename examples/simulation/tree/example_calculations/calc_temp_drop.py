"""
This script calculates the heat transfer at the consumer
for a simple tree network.
"""
import os
import pandas as pd
import math
import numpy as np

path_file = os.path.dirname(__file__)
path = os.path.abspath(os.path.join(path_file, os.pardir))
input_data = os.path.join(path, 'input')
result_path = os.path.join(path, 'expected_results/sequences')


def read_data(input_value):
    """
    This function is reading the data of a csv with a name given as input value
    """
    return pd.read_csv(os.path.join(input_data, input_value + '.csv'), index_col=0)


# Read input data for every csv component
edges = read_data('edges')
temp_drop = pd.read_csv(input_data + '/sequences/consumers-temperature_drop.csv')
mass_flow = pd.read_csv(input_data + '/sequences/consumers-mass_flow.csv')

# Constants for calculation
t_env = 20 + 273.15                                                                 # [K]
t_prod_i = pd.DataFrame(data={'t_prod_i': (130 + 273.15)*np.ones(len(mass_flow))})  # [K] Temperature at the producer
c = 4190                                                                            # [J/kg*K]
pi = math.pi

# Initialize variables of type dataframe (needed for later calculations)
U_spec, t_cons_i, t_cons_r, t_fork_r, Q_loss_i, Q_loss_r, Q_cons, Q_loss_glob = \
    [pd.DataFrame() for variable in range(8)]

# Adjust mass flows and temp drop to a dataframe containing all data in correct order
# Get mass flows of all consumers
mass_flow_total = mass_flow.iloc[:, 1:]
# Rename the columns to edges naming convention
mass_flow_total.columns = ['1', '2']
# Calculate producer mass flow as sum of consumer mass flows
mass_flow_total['0'] = mass_flow_total['1'] + mass_flow_total['2']
# Change order of columns for later calculation
mass_flow_total = mass_flow_total[['0', '1', '2']]

# Get temperature drop of all consumers
temp_drop = temp_drop.iloc[:, 1:]
temp_drop = temp_drop.rename(columns={'0': '1', '1': '2'})  # Rename the columns to edges naming convention


def calc_temp_heat_loss(t_in, index):
    """
    This function calculates the pipe's outlet temperature
    out of the inlet temperature due to heat losses
    :param t_in:
    :param index:
    :return: t_out
    """
    t_out = t_env + (t_in - t_env) * np.exp(- edges['heat_transfer_coefficient_W/mK'].iloc[index]
                                            * pi
                                            * edges['diameter_mm'].iloc[index] / 1000
                                            * edges['lenght_m'].iloc[index] /
                                            (c * mass_flow_total[str(index)]))
    return t_out


def calc_heat_loss(m, t_in, t_out):
    """
    This function calculates heat losses

    Needs to be adapted in case heat capacity is not constant as assumed

    :param m: mass flow [kg/s]
    :param t_in: inlet temperature [K]
    :param t_out: outlet temperature [K]
    :return: heat flow [W]
    """
    return m * c * (t_in - t_out)


# Calculate inlet temperature at fork
t_fork_i = pd.DataFrame(data={'0': calc_temp_heat_loss(t_prod_i['t_prod_i'], 0)})

# Calculate heat loss at edge from producer to fork
Q_loss_i['0'] = calc_heat_loss(mass_flow_total['0'], t_prod_i['t_prod_i'], t_fork_i['0'])

for index in list(temp_drop):
    # Calculate inlet temperature at consumers
    t_cons_i[index] = calc_temp_heat_loss(t_fork_i['0'], int(index))
    # Calculate return temperature at consumers
    t_cons_r[index] = t_cons_i[index] - temp_drop[index]
    # Calculate return temperature at fork
    t_fork_r[index] = calc_temp_heat_loss(t_cons_r[index], int(index))
    # Calculate heat losses at edge from fork to consumer
    Q_loss_i[index] = calc_heat_loss(mass_flow_total[index], t_fork_i['0'], t_cons_i[index])
    # Calculate heat losses at edge from consumer to fork
    Q_loss_r[index] = calc_heat_loss(mass_flow_total[index], t_cons_r[index], t_fork_r[index])
    # Calculate heat transfer at consumers with temperature drop
    Q_cons[index] = calc_heat_loss(mass_flow_total[index], t_cons_i[index], t_cons_r[index])

# Calculate temperature of mixture at fork return
# Note with these input values irrelevant because the temperatures coming from the consumers are the same.
# Needs to be adapted in case capacity is not constant as assumed
t_fork_r_mix = pd.DataFrame(data={'0': (mass_flow_total['1'] * t_fork_r['1'] +
                                        mass_flow_total['2'] * t_fork_r['2']) / mass_flow_total['0']})

# Calculate return temperature at producer
t_prod_r = pd.DataFrame(data={'0': calc_temp_heat_loss(t_fork_r_mix['0'], int('0'))})

# Calculate heat loss at edge from fork to producer
Q_loss_r['0'] = calc_heat_loss(mass_flow_total['0'], t_fork_r_mix['0'], t_prod_r['0'])

# Calculate total heat losses (inlet and return)
Q_loss = Q_loss_i + Q_loss_r

# Calculate global heat losses
Q_loss_glob = pd.DataFrame(data={'losses': np.zeros(len(mass_flow_total))})
for index, node in enumerate(mass_flow_total):
    Q_loss_glob['losses'] = Q_loss_glob['losses'] + Q_loss[str(index)]


# Print results
def parameters():
    parameter = {
            'Mass flow [kg/s]': mass_flow_total,
            'Inlet temperature at producer T_prod_i [K]': t_prod_i,
            'Return temperature at producer T_prod_r [K]': t_prod_r,
            'Inlet temperature at fork T_fork_i [K]': t_fork_i,
            'Return temperature at fork T_fork_r [K]': t_fork_r_mix,
            'Inlet temperature at consumer T_c_i [K]': t_cons_i,
            'Return temperature at consumer T_c_out [K]': t_cons_r,
            'Heat losses Q_loss [W]': Q_loss,
            'Global heat losses Q_loss_glob [W]': Q_loss_glob,
            'Heat transfer at consumers Q [W]': Q_cons,

        }
    return parameter


parameter = parameters()


def print_parameters():
    dash = '-' * 60

    print('\n' + dash)
    print('Results at producer (0), consumer 1 (1) and consumer 2 (2)')
    print(dash)

    for name, param in parameter.items():
        print(name + '\n' + str(param) + '\n\n')

    print(dash)


print_parameters()


# Save results to csv
for name, param in parameter.items():
    param.insert(0, 'snapshot', np.arange(len(mass_flow_total)))


result_name = ['producers-temp_return.csv', 'forks-temp_inlet.csv', 'forks-temp_return.csv',
               'consumers-temp_inlet.csv', 'consumers-temp_return.csv', 'edges-heat_losses.csv',
               'global-heat_losses.csv']

result_list = list(parameter.keys())[2:9]

for index, name in enumerate(result_list):
    parameter[name].to_csv(os.path.join(result_path, result_name[index]), index=False)



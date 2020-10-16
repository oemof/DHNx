"""
This script calculates the pressure losses and the needed power for the pump
in a simple tree network.

The assumption of three fittings has been made:
1. Tee connector at the fork
2. Valve at the consumer 1
3. Valve at the consumer 2

"""
import os
import pandas as pd
import math
import numpy as np

path_file = os.path.dirname(__file__)
path = os.path.abspath(os.path.join(path_file, os.pardir, os.pardir, os.pardir))
input_data = os.path.join(path, 'examples', 'simulation', 'tree')
result_path = os.path.join(path_file, 'sequences')

if not os.path.exists(result_path):
    os.mkdir(result_path)


def read_data(input_value):
    """
    This function is reading the data of a csv with a name given as input value
    """
    return pd.read_csv(os.path.join(input_data, input_value + '.csv'), index_col=0)


# Read input data for every csv component
consumers = read_data('consumers')
pipes = read_data('pipes')
forks = read_data('forks')
producers = read_data('producers')
mass_flow = pd.read_csv(input_data + '/sequences/consumers-mass_flow.csv')

# Constants for calculation
rho = 971.78                # [kg/m3] TODO: later the density could be variable and calculated with CoolProp
epsilon = 0.01              # [mm]
zeta_tee_connect = 0.75     # [-] Rough estimate of Tee connector: WJ Beek - Transport Phenomena (1999)
zeta_tee_separation = 2     # [-] Rough estimate of Tee connector: WJ Beek - Transport Phenomena (1999)
zeta_valve = 3.3            # [-] VDI Wärmeatlas für Nennweite von 50 mm
mu = 0.35                   # [mPa*s]
eta_pump = 1                # [-]
g = 9.81                    # [m/s2]
pi = math.pi

# Initialize variables of type dataframe (needed for later calculations)
v, re, lambda_simp, lambda_adv, dp_diss, dp_loc, dp_loc_tee_i, dp_loc_tee_r, dp_loc_valve, dp_hyd, dp = \
    [pd.DataFrame() for variable in range(11)]

# Adjust mass flows to a dataframe containing all mass flows in correct order
# Get mass flows of all consumers
mass_flow_total = mass_flow.iloc[:, 1:]
# Rename the columns to pipes naming convention
mass_flow_total.columns = ['1', '2']
# Calculate producer mass flow as sum of consumer mass flows
mass_flow_total['0'] = mass_flow_total['1'] + mass_flow_total['2']
# Change order of columns for later calculation
mass_flow_total = mass_flow_total[['0', '1', '2']]


for index, node in enumerate(mass_flow_total):
    # Calculation of the velocity v
    v[str(index)] = 4 * mass_flow_total[str(node)] / (rho * pi * (pipes['diameter_mm'].iloc[index] / 1000) ** 2)

    # Calculation of Re number
    re[str(index)] = pipes['diameter_mm'].iloc[index] / 1000 * v[str(index)] * rho / (mu/1000)
    # Calculation of lambda with simple approach
    lambda_simp[str(index)] = 0.07 * re[str(index)]**-0.13 * (pipes['diameter_mm'].iloc[index] / 1000)**-0.14
    # Calculation of lambda with advanced approach
    lambda_adv[str(index)] = 1.325 / np.log(epsilon/(1000*3.7*(pipes['diameter_mm'].iloc[index] / 1000))
                                            + 5.74/(re[str(index)]**0.9))**2
    # Calculate distributed pressure losses with Darcy-Weissbach-equation
    dp_diss[str(index)] = lambda_simp[str(index)] * rho * pipes['length_m'].iloc[index] * v[str(index)]**2 /\
                          (2 * (pipes['diameter_mm'].iloc[index] / 1000))
    # Calculate local pressure losses resulted from separating Tee (T-Stück) -> i - inlet
    # Localized Pressure losses only occur in the outlet pipes of the tee separator
    if node == '0':
        dp_loc_tee_i[str(index)] = 0 * zeta_tee_separation * v[str(index)] ** 2 * rho / 2
    elif node != '0':
        dp_loc_tee_i[str(index)] = zeta_tee_separation * v[str(index)] ** 2 * rho / 2
    # Calculate local pressure losses resulted from connecting Tee (T-Stück) -> r - return
    # Localized Pressure losses only occur in the outlet pipes of the tee connector
    if node == '0':
        dp_loc_tee_r[str(index)] = zeta_tee_connect * v[str(index)] ** 2 * rho / 2
    elif node != '0':
        dp_loc_tee_r[str(index)] = 0 * zeta_tee_connect * v[str(index)] ** 2 * rho / 2
    # Calculate local pressure losses resulted from consumer valves
    if node == '0':
        dp_loc_valve[str(index)] = 0 * v[str(index)] ** 2 * rho / 2     # At producer no valve -> zeta = 0
    elif node != '0':
        dp_loc_valve[str(index)] = zeta_valve * v[str(index)] ** 2 * rho / 2

# Calculate distributed pressure losses for inlet and return direction (dp_diss * 2)
dp_diss = dp_diss * 2

# Calculate sum of local pressure losses
dp_loc_tee = dp_loc_tee_i + dp_loc_tee_r
dp_loc = dp_loc_tee

# Calculate hydrostatic pressure difference
dp_hyd['0'] = - rho * g * abs(producers['m_over_NHN'][0] - forks['m_over_NHN'][0]) * v['0']**0
dp_hyd['1'] = - rho * g * abs(forks['m_over_NHN'][0] - consumers['m_over_NHN'].iloc[0]) * v['1']**0
dp_hyd['2'] = - rho * g * abs(forks['m_over_NHN'][0] - consumers['m_over_NHN'].iloc[1]) * v['2']**0

# Calculate total pressure loss
dp = dp_diss + dp_loc + dp_hyd

# Find the consumer with maximum pressure losses
max_pressure_losses = max(dp.loc[:, '1':])

# Calculate global pressure loss
dp_glob = pd.DataFrame(data={'losses': np.zeros(len(mass_flow_total))})
dp_glob['losses'] = dp_glob['losses'] + dp['0'] + dp[max_pressure_losses]

# Calculate pump power
p_el_pump = pd.DataFrame(data={'0': np.zeros(len(mass_flow_total))})

for index, node in enumerate(v):
    p_el_pump['0'] = p_el_pump['0'] + 1 / eta_pump * dp[str(index)] / rho * mass_flow_total[str(index)]


# Print results
def parameters():
    parameter = {
            'Velocity v [m/s]': v,
            'Reynolds Re [-]': re,
            'Lambda λ (simple approach) [-]': lambda_simp,
            'Lambda λ (advanced approach) [-]': lambda_adv,
            'Distributed pressure losses ∆p_dis [kg/ms2]': dp_diss,
            'Local losses due to tee ∆p_loc,tee [kg/ms2]': dp_loc_tee,
            'Local losses due to valve ∆p_loc,valve [kg/ms2]': dp_loc_valve,
            'Total local losses ∆p_loc [kg/ms2]': dp_loc,
            'Hydrostatic losses ∆p_hyd [kg/ms2]': dp_hyd,
            'Total pressure losses ∆p [kg/ms2]': dp,
            'Global pressure losses ∆p_glob [kg/ms2]': dp_glob,
            'Total electrical energy pump P_el [W]': p_el_pump,
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
#for name, param in parameter.items():
#    param.insert(0, 'snapshot', np.arange(len(mass_flow_total)))

result_name = ['pipes-pressure_losses.csv', 'global-pressure_losses.csv', 'producers-pump_power.csv']
result_list = list(parameter.keys())[-3:]

for index, name in enumerate(result_list):
    parameter[name].to_csv(os.path.join(result_path, result_name[index]), index=False)


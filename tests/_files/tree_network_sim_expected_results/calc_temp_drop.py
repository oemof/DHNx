# -*- coding: utf-8

"""
This script calculates the heat transfer at the consumer
for a simple tree network.
"""
import os
import pandas as pd
import math
import numpy as np

path_file = os.path.dirname(__file__)
path = os.path.abspath(os.path.join(path_file, os.pardir, os.pardir, os.pardir))
input_data = os.path.join(path, "examples", "simulation", "tree")
result_path = os.path.join(path_file, "sequences")

if not os.path.exists(result_path):
    os.mkdir(result_path)


def read_data(input_value):
    r"""
    This function is reading the data of a csv with a name given as input value
    """
    return pd.read_csv(os.path.join(input_data, input_value + ".csv"), index_col=0)


# Read input data for every csv component
pipes = read_data("pipes")
temp_drop = pd.read_csv(input_data + "/sequences/consumers-temperature_drop.csv")
mass_flow = pd.read_csv(input_data + "/sequences/consumers-mass_flow.csv")

# Constants for calculation
t_env = 10  # [°C]
t_prod_i = pd.DataFrame(data={"t_prod_i": 130 * np.ones(len(mass_flow))})  # [°C]
c = 4190  # [J/kg*K]
pi = math.pi

# Initialize variables of type dataframe (needed for later calculations)
U_spec, t_cons_i, t_cons_r, t_fork_r, Q_loss_i, Q_loss_r, Q_cons, Q_loss_glob = [
    pd.DataFrame() for variable in range(8)
]

# Adjust mass flows and temp drop to a dataframe containing all data in correct order
# Get mass flows of all consumers
mass_flow_total = mass_flow.iloc[:, 1:]
# Rename the columns to pipes naming convention
mass_flow_total.columns = ["1", "2"]
# Calculate producer mass flow as sum of consumer mass flows
mass_flow_total["0"] = mass_flow_total["1"] + mass_flow_total["2"]
# Change order of columns for later calculation
mass_flow_total = mass_flow_total[["0", "1", "2"]]

# Get temperature drop of all consumers
temp_drop = temp_drop.iloc[:, 1:]
# Rename the columns to pipes naming convention
temp_drop = temp_drop.rename(columns={"0": "1", "1": "2"})


def calc_temp_heat_loss(t_in, pos):
    r"""
    This function calculates the pipe's outlet temperature
    out of the inlet temperature due to heat losses

    Parameters
    ----------
    t_in : Series
           Temperature entering the pipe
    pos : int
          Position of node

    Returns
    -------
    t_out : Series
            Temperature leaving the pipe
    """
    t_out = t_env + (t_in - t_env) * np.exp(
        -pipes["heat_transfer_coefficient_W/mK"].iloc[pos]
        * pi
        * pipes["diameter_mm"].iloc[pos]
        / 1000
        * pipes["length_m"].iloc[pos]
        / (c * mass_flow_total[str(pos)])
    )
    return t_out


def calc_heat_loss(m, t_in, t_out):
    r"""
    This function calculates heat losses

    Needs to be adapted in case heat capacity is not constant as assumed

    Parameters
    ----------
    m : Series
        Mass flow [kg/s]
    t_in : Series
           Inlet temperature [K]
    t_out : Series
            Outlet temperature [K]

    Returns
    -------
    Heat flow [W]
    """
    return m * c * (t_in - t_out)


# Calculate inlet temperature at fork
t_fork_i = pd.DataFrame(data={"0": calc_temp_heat_loss(t_prod_i["t_prod_i"], 0)})

# Calculate heat loss at pipe from producer to fork
Q_loss_i["0"] = calc_heat_loss(
    mass_flow_total["0"], t_prod_i["t_prod_i"], t_fork_i["0"]
)

for index in list(temp_drop):
    # Calculate inlet temperature at consumers
    t_cons_i[index] = calc_temp_heat_loss(t_fork_i["0"], int(index))
    # Calculate return temperature at consumers
    t_cons_r[index] = t_cons_i[index] - temp_drop[index]
    # Calculate return temperature at fork
    t_fork_r[index] = calc_temp_heat_loss(t_cons_r[index], int(index))
    # Calculate heat losses at pipe from fork to consumer
    Q_loss_i[index] = calc_heat_loss(
        mass_flow_total[index], t_fork_i["0"], t_cons_i[index]
    )
    # Calculate heat losses at pipe from consumer to fork
    Q_loss_r[index] = calc_heat_loss(
        mass_flow_total[index], t_cons_r[index], t_fork_r[index]
    )
    # Calculate heat transfer at consumers with temperature drop
    Q_cons[index] = calc_heat_loss(
        mass_flow_total[index], t_cons_i[index], t_cons_r[index]
    )

# Calculate temperature of mixture at fork return
# Note with these input values irrelevant
# because the temperatures coming from the consumers are the same.
# Needs to be adapted in case capacity is not constant as assumed
t_fork_r_mix = pd.DataFrame(
    data={
        "0": (
            mass_flow_total["1"] * t_fork_r["1"] + mass_flow_total["2"] * t_fork_r["2"]
        )
        / mass_flow_total["0"]
    }
)

# Calculate return temperature at producer
t_prod_r = pd.DataFrame(data={"0": calc_temp_heat_loss(t_fork_r_mix["0"], int("0"))})

# Calculate inlet temperature of nodes
t_nodes_i = pd.DataFrame(
    data={
        "producers-0": t_prod_i["t_prod_i"],
        "forks-0": t_fork_i["0"],
        "consumers-0": t_cons_i["1"],
        "consumers-1": t_cons_i["2"],
    }
)

# Calculate return temperature of nodes
t_nodes_r = pd.DataFrame(
    data={
        "producers-0": t_prod_r["0"],
        "forks-0": t_fork_r_mix["0"],
        "consumers-0": t_cons_r["1"],
        "consumers-1": t_cons_r["2"],
    }
)

# Calculate heat loss at pipe from fork to producer
Q_loss_r["0"] = calc_heat_loss(mass_flow_total["0"], t_fork_r_mix["0"], t_prod_r["0"])

# Calculate total heat losses (inlet and return)
Q_loss = Q_loss_i + Q_loss_r

# Calculate global heat losses
Q_loss_glob = pd.DataFrame(data={"global_heat_losses": np.zeros(len(mass_flow_total))})
for index, node in enumerate(mass_flow_total):
    Q_loss_glob["global_heat_losses"] = (
        Q_loss_glob["global_heat_losses"] + Q_loss[str(index)]
    )


# Print results
def parameters():
    r"""
    Writes results in Dictionary

    Returns
    -------
    parameter : dict
                Dictionary with results
    """
    param_dict = {
        "Mass flow [kg/s]": mass_flow_total,
        "Inlet temperature at producer T_prod_i [°C]": t_prod_i,
        "Return temperature at producer T_prod_r [°C]": t_prod_r,
        "Inlet temperature at fork T_fork_i [°C]": t_fork_i,
        "Return temperature at fork T_fork_r [°C]": t_fork_r_mix,
        "Inlet temperature at consumer T_c_i [°C]": t_cons_i,
        "Return temperature at consumer T_c_out [°C]": t_cons_r,
        "Inlet temperature nodes T_nodes_i [°C]": t_nodes_i,
        "Return temperature nodes T_nodes_r [°C]": t_nodes_r,
        "Heat losses Q_loss [W]": Q_loss,
        "Global heat losses Q_loss_glob [W]": Q_loss_glob,
        "Heat transfer at consumers Q [W]": Q_cons,
    }
    return param_dict


parameter = parameters()


def print_parameters():
    r"""
    Prints the parameters
    """
    dash = "-" * 60

    print("\n" + dash)
    print("Results at producer (0), consumer 1 (1) and consumer 2 (2)")
    print(dash)

    for name, param in parameter.items():
        print(name + "\n" + str(param) + "\n\n")

    print(dash)


print_parameters()


# Save results to csv
for value, params in parameter.items():
    params.insert(0, "snapshot", np.arange(len(mass_flow_total)))


result_name = [
    "pipes-mass_flow.csv",
    "nodes-temp_inlet.csv",
    "nodes-temp_return.csv",
    "pipes-heat_losses.csv",
    "global-heat_losses.csv",
]

result_list = [list(parameter.keys())[0]] + list(parameter.keys())[7:11]

for index, value in enumerate(result_list):
    parameter[value].to_csv(os.path.join(result_path, result_name[index]), index=False)

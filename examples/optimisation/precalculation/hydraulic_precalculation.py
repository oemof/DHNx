import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from dhnx.optimization.precalc_hydraulic import v_max_bisection,\
    calc_mass_flow, calc_power, v_max_secant

df = pd.read_csv("Pipe_data.csv", sep=";")

maximum_pressure_drop = 150  # in Pa/m

# Calculation of maximum velocity
df['v_max [m/s]'] = df.apply(lambda row: v_max_bisection(
    d_i=row['Inner diameter [m]'],
    T_average=row['Temperature level [Celsius]'],
    k=row['Roughness [mm]'],
    p_max=maximum_pressure_drop), axis=1)

# alternative with secant method
df['v_max (secant) [m/s]'] = df.apply(lambda row: v_max_secant(
    d_i=row['Inner diameter [m]'],
    T_average=row['Temperature level [Celsius]'],
    k=row['Roughness [mm]'],
    p_max=maximum_pressure_drop), axis=1)

# Calculation of mass flow
df['Mass flow [kg/s]'] = df.apply(lambda row: calc_mass_flow(
    v=row['v_max [m/s]'], di=row['Inner diameter [m]'],
    T_av=row['Temperature level [Celsius]']), axis=1)

# Calculation of maximum Power
df['P_max [kW]'] = df.apply(lambda row: 0.001 * calc_power(
    T_vl=row['T_forward [Celsius]'],
    T_rl=row['T_return [Celsius]'],
    mf=row['Mass flow [kg/s]']), axis=1)

# Create pipes table for district heating network optimization

# Linear approximation with 1 segment
constants_costs = np.polyfit(df['P_max [kW]'], df['Costs [eur]'], 1)
constants_loss = np.polyfit(df['P_max [kW]'], df['Loss [kW/m]'], 1)

print('Costs constants: ', constants_costs)
print('Loss constants: ', constants_loss)


pipes = pd.DataFrame(
    {
        "label_3": "your-pipe-type-label",
        "active": 1,
        "nonconvex": 1,
        "l_factor": constants_loss[0],
        "l_factor_fix": constants_loss[1],
        "cap_max": df['P_max [kW]'].max(),
        "cap_min": df['P_max [kW]'].min(),
        "capex_pipes": constants_costs[0],
        "fix_costs": constants_costs[1],
    }, index=[0],
)

x_min = df['P_max [kW]'].min()
x_max = df['P_max [kW]'].max()
y_min = constants_costs[0] * x_min + constants_costs[1]
y_max = constants_costs[0] * x_max + constants_costs[1]

fig, ax = plt.subplots()
x = df['P_max [kW]']
y = df['Costs [eur]']
ax.plot(x, y, lw=0, marker="o")
ax.plot(
    [x_min, x_max], [y_min, y_max],
    ls=":", color='r', marker="x"
)
ax.set_xlabel("Transport capacity [kW]")
ax.set_ylabel("Kosten [€/m]")
plt.text(2000, 250, "Linear cost approximation \n"
                    "of district heating pipelines \n"
                    "based on maximum pressure drop \n"
                    "of {:.0f} Pa/m".format(maximum_pressure_drop))
plt.ylim(0, None)
plt.grid(ls=":")
plt.show()

# TODO : Show linear approximation with more segments

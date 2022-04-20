import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from dhnx.optimization.precalc_hydraulic import v_max_bisection, calc_mass_flow, calc_power

df = pd.read_csv("Pipe_data.csv", sep=";")

#Calculation of maximum velocity
df['v_max [m/s]'] = df.apply(lambda row: v_max_bisection(
    d_i=row['Inner diameter [m]'],
    T_average=row['Temperature level [Celsius]'],
    k=row['Roughness [mm]'],
    p_max=row['Max delta p [Pa/m]']), axis=1)

#Calculation of mass flow
df['Mass flow [kg/s]'] = df.apply(lambda row: calc_mass_flow(
    v=row['v_max [m/s]'], di=row['Inner diameter [m]'],
    T_av=row['Temperature level [Celsius]']), axis=1)

#Calculation of maximum Power
df['P_max [kW]'] = df.apply(lambda row: 0.001 * calc_power(
    T_vl=row['T_forward [Celsius]'],
    T_rl=row['T_return [Celsius]'],
    mf=row['Mass flow [kg/s]']), axis=1)

print(df)

constants_costs = np.polyfit(df['P_max [kW]'], df['Costs [eur]'], 1)
constants_loss = np.polyfit(df['P_max [kW]'], df['Loss [W/m]'], 1)

print('Kostenkonstanten: ', constants_costs)
print('Verlustkonstanten: ', constants_loss)

x = df['Mass flow [kg/s]']
y = df['Costs [eur]']
plt.plot(x, y)
plt.xlabel = "Massenstrom (kg/s)"
plt.ylabel = "Kosten (€)"
plt.show()


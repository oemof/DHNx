import numpy as np
import pandas as pd

from dhnx.optimization.precalc_hydraulic import v_max_bisection, calc_mass_flow, calc_power


# d_inner = 0.015   # unit [m]
# T_fluid = 65
# del_p = delta_p(v=0.289, d_i=d_inner, T_medium=T_fluid)   # Pascal [N/m^2]
# v_auslegung_bisection = v_max_bisection(d_i=d_inner, T_average=T_fluid,
#                                         k=0.1, p_max=100)
# v_auslegung_secant = calc_v_max(d_i=d_inner, T_average=T_fluid,
#                                 k=0.1, p_max=100)

df = pd.read_csv("Pipe_data.csv", sep=";")

df['v_max [m/s]'] = df.apply(lambda row: v_max_bisection(
    d_i=row['Inner diameter [m]'],
    T_average=row['Temperature level [Celsius]'],
    k=row['Roughness [mm]'],
    p_max=row['Max delta p [Pa/m]']), axis=1)

df['Mass flow [kg/s]'] = df.apply(lambda row: calc_mass_flow(
    v=row['v_max [m/s]'], di=row['Inner diameter [m]'],
    T_av=row['Temperature level [Celsius]'],
    ), axis=1)

df['P_max [kW]'] = df.apply(lambda row: 0.001*calc_power(
    T_vl=row['T_forward [Celsius]'],
    T_rl=row['T_return [Celsius]'],
    mf=row['Mass flow [kg/s]']
    ), axis=1)
print(calc_power())

#df.to_excel('data_kamp/Waermeleitungen/CaldoPEX_export.xlsx')

constants_costs = np.polyfit(df['P_max [kW]'], df['Costs [eur]'], 1)
constants_loss = np.polyfit(df['P_max [kW]'], df['Loss [W/m]'], 1)

print('Kostenkonstanten: ', constants_costs)
print('Verlustkonstanten: ', constants_loss)

# get linear approximations
# 1) all points
# 2) just double (DN 25 - 75)
# 3) just singel ( > DN 75)

# df_1 = df[df['Rauhigkeit [mm]'] == 0.1]
# df_1_double = df_1[df_1['Innendurchmesser [m]'] < 0.08]
# df_1_single = df_1[df_1['Innendurchmesser [m]'] > 0.08]

# c_double = np.polyfit(df_1_double['P_max [kW]'],
#                       df_1_double['Kosten [eur]'], 1)

# c_single = np.polyfit(df_1_single['P_max [kW]'],
#                       df_1_single['Kosten [eur]'], 1)







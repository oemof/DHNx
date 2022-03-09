# -*- coding: utf-8

"""
This module is designed to hold functions for pre-calculation of hydraulic
parameters for the district heating network dimensioning.

The aim is to calculate the maximum heat transport capacity in [kW]
of pipelines given a maximum pressure drop per meter, roughness of the pipes
inner surface, and an estimatet delta T of the forward and return pipes.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

from CoolProp.CoolProp import PropsSI
import numpy as np
from scipy.optimize import fsolve
import math

# Berechnung Druckverlust siehe:
#   - http://www.math-tech.at/Beispiele/upload/gra_Druckverlust_in_Rohrleitungen.PDF
#   - https://www.schweizer-fn.de/stroemung/rauhigkeit/rauhigkeit.php


def delta_p(v, d_i, k=0.1, T_medium=90, length=1,
            pressure=1, R_crit=2320, fluid='IF97::Water'):

    """Function to determine the pressure loss in the DHN pipes.

    # Text :func:`transition_eq`


    Parameters
    ----------
    v : numeric
        volume [m³]

    d_i : numeric
        inner pipe diameter [m]

    k : numeric
        roughness of inner pipeline surface [mm]

    T_medium : numeric
        fluid temperature [°C]

    length : numeric
        length of the pipe [m]

    pressure : numeric
        pressure in the pipe [bar]

    R_crit : numeric
        critical reynolds number beetween laminar and turbulent flow

    fluid : str
        name of the fluid used

    Returns
    -------

    """

    def glatt_eq(x):
        """

        Parameters
        ----------
        x : numeric

        Returns
        -------

        """
        # http://www.math-tech.at/Beispiele/upload/gra_Druckverlust_in_Rohrleitungen.PDF
        # Formel von Prandtl und v. Karman
        # FM FS S.12 - Technische Strömung - (a)
        #
        return x - 2 * np.log10(R_e / (x * 2.51))

    def transition_eq(x):
        """

        Parameters
        ----------
        x : numeric


        Returns
        -------

        """
        # FM FS S.13 - erste Formel (Übergangsbereich glatt-rau)
        # http://www.math-tech.at/Beispiele/upload/gra_Druckverlust_in_Rohrleitungen.PDF
        # 65 < Re * k/d < 1300
        # TODO: Formel überprüfen
        return x + 2 * np.log10((2.51 * x) / R_e + k / (3.71 * d_i))

    k = k * 0.001

    # get density of water [kg/m^3]
    d = PropsSI('D', 'T', T_medium + 273.15, 'P', pressure * 101325, fluid)
    # dynamic viscosity eta [kg/(m*s)]
    d_v = PropsSI('V', 'T', T_medium + 273.15, 'P', pressure * 101325, fluid)
    k_v = d_v / d     # kinematic viskosity [m^2/s]

    # Reynodszahl
    R_e = (v * d_i) / k_v

    if R_e < R_crit:  # laminare Strömung

        lam = 64 / R_e      # S. 216 - (11.9), ISBN  978-3-540-73726-1
        d_p = lam * length / d_i * d / 2 * v ** 2

    else:  # turbulente Strömung

        if R_e * k / d_i < 65:
            # ==> Rohr hydraulisch glatt

            if R_e < 10**5:
                # siehe Fluidmechanik Formelsammlung, S.12 (2.)
                # nach Prandtl
                lam = 0.3164 * R_e ** (-0.25)

            elif R_e >= 10**5 and R_e < 10**6:
                # Nikuradse:
                # http://www.math-tech.at/Beispiele/upload/gra_Druckverlust_in_Rohrleitungen.PDF
                # Fluidmechanik I FS: S.12,
                lam = 0.0032 + 0.221 * R_e ** (-0.237)

            else:
                # Re > 10^6 ???
                # Prandtl and Karman / laut FM FS Nikurdase
                # Näherungswert als Startwert für fsolve
                lam_init = 0.3164 / (R_e ** 0.25)

                args = {
                    R_e: R_e,
                }

                x = fsolve(glatt_eq, x0=lam_init, args=args)
                lam = 1 / x[0] ** 2

        elif R_e * k / d_i > 1300:
            # ==> Rohr hydraulisch rau
            # entsprich FM, FS. S.13 zweite Formel von oben
            lam = (1 / (-2 * np.log10(k / (3.71 * d_i)))) ** 2

        else:
            # ==> Übergangsbereich 65 < Re * k/d < 1300

            # Näherung
            lam_init = 0.25 / R_e ** 0.2
            # FM FS S.13 - erste Formel (Übergangsbereich glatt-rau)
            # http://www.math-tech.at/Beispiele/upload/gra_Druckverlust_in_Rohrleitungen.PDF
            # 65 < Re * k/d < 1300
            x = fsolve(transition_eq, x0=lam_init)
            lam = 1 / x[0] ** 2

        d_p = lam * length / d_i * d / 2 * v ** 2

    return d_p


def calc_v(vol_flow, d_i):
    r"""
    Calculates the velocity for a given volume flow and inner diameter of a pipe.

    Formula
    -------
    .. calc_v_equation:

    :math:`v_{flow}=\frac{\dot{V}}{(\frac{d_i}{2})^2*\pi}`

    Parameters
    ----------
    vol_flow: numeric
        :math:`\dot{V}`: volume flow [m³/h]

    d_i: numeric
        :math:`d_i`: inner diameter [m]

    Returns
    -------
    flow velocity [m/s] : numeric

    """
    return vol_flow / ((d_i * 0.5)**2 * math.pi * 3600)


def calc_v_max(d_i, T_average, k=0.1, p_max=100, p_epsilon=1,
               v_0=1, v_1=2,
               pressure=1, fluid='IF97::Water'):
    """

    Parameters
    ----------
    d_i : numeric
        inner diameter [m]

    T_average : numeric
        average temperature [°C]

    k : numeric
        roughness of inner pipeline surface [mm]

    p_max : numeric
        maximum pressure drop in pipeline [Pa]

    p_epsilon : numeric
        accuracy [Pa]

    v_0 : numeric
        initial guess for maximum flow velocity [m/s] #von v_init übernommen

    v_1 : numeric
        ??? #keine vorlage

    pressure : numeric
        pressure level [bar]

    fluid : str
        type of fluid, default: 'IF97::Water'

    Returns
    -------
    v_max : numeric
        maximum flow velocity [m/s]

    """
    p_new = 0
    v_new = 0
    n = 0
    while n < 100:
        n += 1

        p_0 = delta_p(v_0, k=k, d_i=d_i, T_medium=T_average,
                      pressure=pressure, fluid=fluid)

        p_1 = delta_p(v_1, k=k, d_i=d_i, T_medium=T_average,
                      pressure=pressure, fluid=fluid)

        v_new = v_1 - (p_1 - p_max) * (v_1 - v_0) / (p_1 - p_0)

        p_new = delta_p(v_new, k=k, d_i=d_i, T_medium=T_average,
                        pressure=pressure, fluid=fluid)

        # print(n, ' P_0 [Pa]: ', p_0, 'v_0 [m/s]: ', v_0)
        # print(n, ' P_1 [Pa]: ', p_1, 'v_1 [m/s]: ', v_1)
        # print(n, ' P_new [Pa]: ', p_new, 'v_new [m/s]: ', v_new)
        # print(' --- ')

        if abs(p_new - p_max) < p_epsilon:
            break

        else:
            v_0 = v_1
            v_1 = v_new

    print('Number of Iterations: ', n)
    print('Resulting pressure drop ', p_new)
    print('Resulting velocity: ', v_new)

    return v_new


def v_max_bisection(d_i, T_average, k=0.1, p_max=100,
                    p_epsilon=0.1, v_epsilon=0.001,
                    v_0=0.01, v_1=10,
                    pressure=1, fluid='IF97::Water'):
    """

    Parameters
    ----------
    d_i : numeric
        inner diameter [m]

    T_average : numeric
        average temperature [°C]

    k : numeric
        roughness of inner pipeline surface [mm]

    p_max : numeric
        maximum pressure drop in pipeline [Pa]

    p_epsilon : numeric
        accuracy [Pa]

    v_epsilon : numeric
        accuracy [m/s] #so richtig?

    v_0  : numeric
        initial guess for maximum flow velocity [m/s]

    v_1 : numeric
        #???
    pressure : numeric
        pressure level [bar]

    fluid : str
        type of fluid, default: 'IF97::Water'

    Returns
    -------
    v_max : numeric
        maximum flow velocity

    """
    """
    :param d_i:         [m]     inner diameter
    :param T_average:   [°C]    average temperature
    :param k:           [mm]    roughness of inner pipeline surface
    :param p_max:       [Pa]    maximum pressure drop in pipeline
    :param p_epsilon:   [Pa]    accuracy
    :param v_init:      [m/s]   initial guess for maximum flow velocity
    :param pressure:    [bar]   pressure level
    :param fluid:       [-]     type of fluid, default: 'IF97::Water'
    :return:            [m/s]   maximum flow velocity
    """

    p_0 = delta_p(v_0, k=k, d_i=d_i, T_medium=T_average,
                  pressure=pressure, fluid=fluid)

    p_1 = delta_p(v_1, k=k, d_i=d_i, T_medium=T_average,
                  pressure=pressure, fluid=fluid)

    if (p_0 - p_max) * (p_1 - p_max) >= 0:
        print('The initial guesses are not assumed right!')
        return

    p_new = 0
    v_new = 0
    n = 0
    while n < 200:
        n += 1

        p_0 = delta_p(v_0, k=k, d_i=d_i, T_medium=T_average,
                      pressure=pressure, fluid=fluid)

        p_1 = delta_p(v_1, k=k, d_i=d_i, T_medium=T_average,
                      pressure=pressure, fluid=fluid)

        v_new = 0.5 * (v_1 + v_0)

        p_new = delta_p(v_new, k=k, d_i=d_i, T_medium=T_average,
                        pressure=pressure, fluid=fluid)

        # print(n, ' v_0 [m/s]: ', v_0, ' P_0 [Pa]: ', p_0)
        # print(n, ' v_n [m/s]: ', v_new, ' P_n [Pa]: ', p_new)
        # print(n, ' v_1 [m/s]: ', v_1, ' P_1 [Pa]: ', p_1)
        # print('--- ')

        if abs(p_new - p_max) < p_epsilon:
            print('p_epsilon criterion achieved!')
            break

        if abs(v_1 - v_0) < v_epsilon:
            print('v_epsilon criterion achieved!')
            break

        else:
            if (p_0 - p_max) * (p_new - p_max) < 0:
                v_1 = v_new
            else:
                v_0 = v_new

    print('Number of Iterations: ', n)
    print('Resulting pressure drop: ', p_new)
    print('Resulting velocity: ', v_new)

    return v_new


def calc_power(T_vl=80, T_rl=50, mf=3, p=101325):
    r"""
    Function to calculate the thermal power based on mass flow and temperature difference.

    Formula
    -------
    .. calc_power_equation:

    :math:`P_{th} = \dot{m} \cdot (c_{p_{VL}} \cdot T_{VL} - c_{p_{RL}} \cdot T_{RL})`

    Parameters
    ----------
    T_vl: numeric
        :math:`T_{VL}`: forward temperature [°C]

    T_rl: numeric
        :math:`T_{RL}`: return temperature [C°]

    mf: numeric
        :math:`\dot{m}`: mass flow [kg/s]

    p: numeric
        :math:`p`: pressure [Pa]

    Returns
    -------
    thermal power [W] : numeric

    """
    cp_vl = PropsSI('C', 'T', T_vl + 273.15, 'P', p, 'IF97::Water')

    cp_rl = PropsSI('C', 'T', T_rl + 273.15, 'P', p, 'IF97::Water')

    return mf * (cp_vl * (T_vl + 273.15) - cp_rl * (T_rl + 273.15))


def calc_mass_flow(v, di, T_av, p=101325):
    r"""
    Calculates the mass flow in a pipe for a given density, diameter and flow velocity.
    The average temperature is needed for a correct value of the density.

    Formula
    -------
    .. calc_mass_flow_equation:

    :math:`\dot{m} = \pi \rho_{T_av}  v  \big( \frac{d_i}{2}  \big) ^2`

    Parameters
    ----------
    v : numeric
        :math:`v`: flow velocity [m/s]

    di : numeric
        :math:`d_i`: inner diameter [m]

    T_av : numeric
        :math:`T_av`: temperature level [°C]

    p: numeric
        :math:`p`: pressure [Pa]

    Returns
    -------
    mass flow [kg/s] : numeric

    """
    rho = PropsSI('D', 'T', T_av + 273.15, 'P', p, 'IF97::Water')

    return rho * v * (0.5 * di) ** 2 * math.pi


def calc_mass_flow_P(P, T_av, delta_T, p=101325):
    r"""
    Calculates the mass flow in a pipe for a given power and heat difference.
    The average temperature is needed for a correct value of the heat capacity.

    Formula
    -------
    .. calc_mass_flow_P_equation:

    :math:`\dot{m} = \frac{P}{c_{P_{T_{av}}} \cdot \Delta T}`

    Parameters
    ----------
    P : numeric
        :math:`P`: power [W]

    T_av : numeric
        :math:`T_{av}`: average temperature [°C]

    delta_T : numeric
        :math:`\Delta T`: temperature difference [K]

    p: numeric
        :math:`p`: pressure [Pa]

    Returns
    -------
    mass flow [kg/s]: numeric

    """
    cp = PropsSI('C', 'T', T_av + 273.15, 'P', p, 'IF97::Water')

    return P / (cp * delta_T)


def calc_v_mf(mf, di, T_av, p=101325):
    r"""
    Calculates the flow velocity for a given mass flow and inner diameter.
    The average temperature is needed for a correct value of the density.

    Formula
    -------
    .. calc_v_mf_equation:

    :math:`v = \frac{\dot{m}}{\pi \rho \cdot \big( \frac{d_i}{2} \big)^2 }`

    Parameters
    ----------
    mf : numeric
        :math:`dot{m}`: mass flow [kg/s]

    di : numeric
        :math:`d_i`: inner diameter [m]

    T_av : numeric
        :math:`T_{av}`: average temperature [°C]

     p: numeric
        :math:`p`: pressure [Pa]

    Returns
    -------
    flow velocity [m/s]: numeric

    """
    rho = PropsSI(
        'D', 'T', T_av + 273.15, 'P', p, 'IF97::Water')  # [kg/m^3]

    return mf / (rho * (0.5 * di) ** 2 * math.pi)


def calc_pipe_loss(temp_average, u_value, temp_ground=10):
    r"""
    Calculates the heat loss of a DHS pipe trench.

    Formula
    -------
    .. calc_pipe_loss_equation:

    :math:`P_{loss} = (T_{average} - T_{ground}) \cdot U`

    Parameters
    ----------
    temp_average : float
        :math:`T_{average}`: Average temperature of medium in
        (if u_value relates to forward and return pipe,
        the average temperature of forward and return must be given.)
    u_value : float
        :math:`U`: Heat transmission coefficient of whole trench in W/(m*K)
        (u_value of forward and return pipe must be summed up, if total
        heat loss should be calculated.)
    temp_ground : float
        :math:`T_{ground}`: Temperature of surrounding, e.g. ground.

    Returns
    -------
    Heat loss of pipe trench [W/m]: float
    """
    return (temp_average - temp_ground) * u_value

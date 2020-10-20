.. _simulation_models_label:

~~~~~~~~~~~~~~~~~
Simulation models
~~~~~~~~~~~~~~~~~

For a more detailed representation of temperature effects and pressure losses in the district
heating network, linear optimization models do not suffice. In this situation, a simulation model
can be the right choice.

Scope
-----

The following questions can be addressed using a simulation model:

* How do the heat losses in the network depend on the temperatures of inlet and return pipes and
  ambient temperature?
* How much energy is necessary for the pumps to overcome the pressure losses in the network?
* How do these properties behave if the supply temperatures change?

To answer these questions, data has to be present or assumptions have to be made about the pipe's
physical properties and the temperature drop at the consumers. Have a look at the
:ref:`overview table <simulation_model_table_label>` to learn about all the variables and
parameters involved.

Conversely, if these are not known, running an optimization model would be the better choice. It
is also possible to couple the two approaches, running an optimization first and then investigating
the detailed physical behaviour. To learn about this option, please refer to the section
:ref:`model coupling <model_coupling_label>`.

Currently, the available simulation model does not handle transient states (i.e. propagation of
temperature fronts through the pipes). The model evaluates a steady state of the hydraulic and
thermal physical equations. This also means that consecutive time steps are modelled independently
and the behaviour of thermal storages cannot be represented. A dynamic simulation model may be
implemented at a later point in time.


Usage
-----

To use DHNx for a simulation, you need to provide input data in a defined form. The basic
requirements are the same for all :class:`ThermalNetwork` s, but some input data is specific to the
simulation.

.. code-block:: txt

    tree
    ├── consumers.csv
    ├── pipes.csv
    ├── forks.csv
    ├── producers.csv
    └── sequences
        ├── consumers-mass_flow.csv
        ├── consumers-temperature_drop.csv
        ├── environment-temp_env.csv
        └── producers-temp_inlet.csv


To run a simulation, create a :class:`ThermalNetwork` from the input data and simulate:

.. code-block:: python

    import dhnx

    thermal_network = dhnx.network.ThermalNetwork('path-to-input-data')

    thermal_network.simulate()


Figure 1 shows a sketch of a simple district heating network that illustrates how the variables that
are determined in a simulation model run are attributed to different parts of a network. Pipes have
the attributes mass flows, heat losses and pressure losses (distributed and localized). Temperatures
of inlet and return flow are attributed to the different nodes. Pump power belongs to the producers
which are assumed to include the pumps. Variables that describe the network as a whole are global
heat losses and global pressure losses.

.. 	figure:: _static/radial_network_details.svg
   :width: 70 %
   :alt: radial_network_details.svg
   :align: center

   Fig. 1: Schematic of a simple district heating network and the relevant variables for simulation.


The above-mentioned variables can be found in the results of a simulation, which come in the
following structure:

.. code-block:: txt

    results
    ├── global-heat_losses.csv
    ├── global-pressure_losses.csv
    ├── nodes-temp_inlet.csv
    ├── nodes-temp_return.csv
    ├── pipes-dist_pressure_losses.csv
    ├── pipes-heat_losses.csv
    ├── pipes_loc_pressure_losses.csv
    ├── pipes-mass_flow.csv
    └── producers-pump_power.csv


Underlying Concept
------------------

.. _simulation_model_table_label:

.. csv-table::
   :header-rows: 1
   :delim: ;
   :file: _static/simulation_models.csv



The following equations are related to a single pipe.

Hydraulic equations
~~~~~~~~~~~~~~~~~~~

A pressure difference between two ends of a pipe occurs because of three effects:

* distributed pressure losses along the pipe's inner surface
* local pressure losses at distinct items,
* hydrostatic pressure differences because of a difference in height.

All three effects can be captured in this formula:

.. math::
    \Delta p = \Delta p_{loc} + \Delta p_{dis} + \Delta p_{hydrostatic}

**Distributed pressure losses**

The Darcy-Weissbach-equation describes distributed pressure losses
:math:`\Delta p_{dis}` inside the pipe:

.. math::
    \Delta p_{dis} = \lambda \rho \frac{L}{2D} v^2.


Together with the flow velocity

.. math::
    v = \frac{4 \dot{m}}{\rho \pi D^2}

it can be written to:

.. math::
    \Delta p_{dis} = \lambda \frac{8 L}{\rho \pi^2 D^5} \dot{m}^2,


where the darcy friction factor :math:`\lambda = \lambda(Re, \epsilon, D)` depends on the Reynolds
number :math:`Re:`, the pipe's surface roughness :math:`\epsilon` and the pipe’s inner diameter
:math:`D`. The Reynolds number is a dimensionless quantity characterizing fluid flows and is defined
as follows:

.. math::
    Re = \frac{Dv\rho}{\mu}.

:math:`\mu` is the dynamic viscosity of water.

In a pipe, flow is laminar if :math:`Re` < 2300 and turbulent if :math:`Re` > 4000.
In district heating pipes, flow is usually turbulent. The turbulent flow regime can be further
distinguished into smooth, intermediate and rough regime depending on the pipe's surface roughness.

[1] provides the following approximation formula for :math:`\lambda`:

.. math::
    \lambda = 0.07 \cdot Re ^{-0.13} \cdot D^{-0.14}.

A more accurate approximation of the Colebrook-White-equation for flow in pipes is given by this
formula:

.. math::
    \lambda = \frac{1.325}{(ln(\frac{\epsilon}{3.7D} + \frac{5.74}{Re^{0.9}}))^2}.

**Local pressure losses**

Local pressure losses are losses at junction elements, angles, valves etc. They are described by
the localized pressure loss coefficient :math:`\zeta`:

.. math::
    \Delta p_{loc} = \zeta \frac{v^2}{2} \rho

It is assumed that each fork has a tee installed. According to [2], localized pressure losses occur
downstream of the element that causes these losses. The values of the localized pressure loss
coefficient :math:`\zeta` were taken from [3]. In case of a tee which splits the stream,
:math:`\zeta` is 2. In case the streams join, :math:`\zeta` is 0.75.

It is also assumed that each consumer has a valve installed. Due to the complexity of determining
the localized pressure loss coefficients, these losses have not been considered so far.

**Hydrostatic pressure difference**

The hydrostatic pressure difference is calculated as follows:

.. math::
    \Delta p_{hydrostatic} = - \rho g \Delta h


**Pump power**

The mass flow in the pipes is driven by the pressure difference that is generated by pumps.
The pumps have to balance the pressure losses inside the pipes. The pump power thus depends on the
pressure difference along the inlet and return along one strand of the network, :math:`\Delta p`,
the mass flow :math:`\dot{m}` and the pump's efficiency
:math:`\eta_{pump} = \eta_{el} \cdot \eta_{hyd}`.

.. math::
    P_{el. pump} = \frac{1}{\eta_{el}\eta_{hyd}}\frac{\Delta p }{\rho} \dot{m}

In a network consisting of several strands, the strand with the largest pressure losses in inlet and
return defines the pressure difference that the pumps have to generate. The underlying assumption is
that the consumers at the end of all other strands adjust their valve to generate the same pressure
losses such that the mass flows that are assumed are met.

Thermal equations
~~~~~~~~~~~~~~~~~

The temperature spread between inlet and return flow defines the amount of heat that is transported
with a given mass flow:

.. math::
    \dot{Q} = \dot{m} \cdot c \cdot \Delta T.


A larger temperature spread allows smaller pipe's diameters, which reduces the
investment cost of new pipes or increases the thermal power of existing pipes.

**Heat losses**

Heat losses depend on temperature level, mass flow and pipe insulation.
Especially the representation of the heat losses depends a lot on the level of detail of a model.
As mentioned above, in the current implementation, the thermal state of the network is assumed to be
in steady state conditions. The temperature at the outlet is calculated as follows:

.. math::
    T_{out} = T_{env} + (T_{in} - T_{env}) \cdot exp\{-\frac{U \pi D L}{c \cdot \dot{m}}\}.


Where :math:`T_{in}` and :math:`T_{out}` are the temperatures at the start and end of the pipe,
:math:`T_{env}` the environmental temperature and :math:`U` the thermal transmittance.


In data documentation of pipes in a district heating, you often find the value of the specific heat
loss per meter :math:`U_{spec} [W/(K m)]`.

.. math::
    U_{spec} = U \cdot \pi D &\text{\hspace{1cm} for single pipes}\\
    U_{spec} = U \cdot 2 \pi D &\text{\hspace{1cm} for double pipes}

The temperature of the return flow at the fork is calculated assuming ideally mixed flows, where no
heat losses occur and the heat capacity is constant. The temperature of the mixed flow
:math:`T_{mix}` is calculated for a number :math:`n` of inlet flows, that are ideally mixed, using
the following equation:

.. math::
    T_{mix} = \frac{\sum\limits_{j=1}^n (\dot{m}_n \cdot T_n)}{\dot{m}_{mix}}

References
----------

.. [1] Chiara Bordin. Mathematical Optimization Applied to Thermal and Electrical Energy Systems.
    PhD thesis, Università di Bologna, 2015.
.. [2] Donald Miller. Internal Flow Systems. 2nd ed. Cranfield, Bedford : BHRA (Information Services), 1990.
.. [3] Beek WJ, Muttzall KM, JW van Heuven. Transport Phenomena. 2nd ed. John Wiley & Sons. Chichester, 1999.

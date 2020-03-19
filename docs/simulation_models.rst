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

* How do the heat losses in the network depend on the temperatures of feed and return pipes and
  ambient temperature?
* How much energy is necessary for the pumps to overcome the pressure losses in the network?
* How do these properties change if the supply temperatures are lowered?

To answer these questions, data has to be present or assumptions have to be made about the pipe's
physical properties and the temperature drop at the consumers. Have a look at the
:ref:`overview table <simulation_model_table_label>` to learn about all the variables and
parameters involved.

Conversely, if these are not known, running an optimization model would be the better choice. It
is also possible to couple the two approaches, running an optimization first and then investigating
the detailled physical behavior. To learn about this option, please refer to the section
:ref:`model coupling <model_coupling_label>`.

Currently, the available do not handle transient states (i.e. propagation of temperature fronts
through the pipes). The simulation model evaluates a steady state of the hydraulic and thermal
physical equations. This also means that consecutive time steps are modelled independently and the
behaviour of thermal storages cannot be represented. A dynamic simulation model may be implemented
at a later point in time.


Usage
-----

.. code-block:: txt

    tree
    ├── consumers.csv
    ├── edges.csv
    ├── forks.csv
    ├── producers.csv
    └── sequences
        ├── consumers-mass_flow.csv
        └── consumers-temperature_drop.csv

.. code-block:: python

    import dhnx

    tnw = dhnx.network.ThermalNetwork()

    tnw.simulate()


.. 	figure:: _static/radial_network_details.svg
   :width: 70 %
   :alt: radial_network_details.svg
   :align: left

   Fig. 1: Schematic





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

Darcy-Weissbach-equation discribes distributed pressure losses
:math:`\Delta p_{dis}` inside the pipes as

.. math::
    \Delta p_{dis} = \lambda \rho \frac{L}{2D} v^2.


Together with the flow velocity

.. math::
    v = \frac{4 \dot{m}}{\rho \pi D^2}

this can be written to

.. math::
    \Delta p_{dis} = \lambda \frac{8 L}{\rho \pi^2 D^5} \dot{m}^2.


Here, :math:`\lambda = \lambda(Re, \epsilon, D)`, depends on
:math:`Re:`, der Rohrrauigkeit (pipe's surface roughness) :math:`\epsilon` und dem Rohrdurchmesser
:math:`D`.
The Reynolds number

.. math:::
    Re = \frac{Dv\rho}{\mu}


is a dimensionless quantity characterizing fluid flows. :math:`\mu` is the dynamic viscosity of
water.

In einem Rohr ist die Strömung bei :math:`Re` < 2300 laminar, bei :math:`Re` > 4000
turbulent. In Fernwärmenetzen ist die Strömung üblicherweise turbulent. Das turbulente
Strömungsregime wird nach Rauigkeit der Rohre weiter in glattes, Übergangs- und raues Regime
unterschieden.

:math:`\lambda` can be calculated using approximation formulas. Bordin2015 nimmt folgende Formel an:

.. math::
    \lambda = 0.07 \cdot Re ^{-0.13} \cdot D^{-0.14}.


Eine genauere Approximation der Colebrook-White-Gleichung für Strömung in Rohren gibt folgende
Formel:

.. math::
    \lambda = \frac{1.325}{(ln(\frac{\epsilon}{3.7D} + \frac{5.74}{Re^{0.9}}))^2}.

**Local pressure losses**

Local pressure losses are losses at Verbindungselementen, Rohrwinkeln, Ventilen etc. Diese werden durch den
Druckverlustbeiwert :math:`\zeta` beschrieben:

.. math::
    \Delta p_{loc} = \zeta \frac{v^2}{2} \rho


In \citet{Bordin2015} wird festgestellt, dass die verteilten Verluste überwiegen. Die Autorin
verwendet
schließlich folgende Näherungsformel mit adäquaten Koeffizienten :math:`K_1` und :math:`K_2`.

.. math::
    \Delta p = \Delta p_{loc} + \Delta p_{dis} = K_1 \dot{m}^2 + K_2 \dot{m}^{1.87}.

**Hydrostatic pressure difference**

.. math::
    \Delta p_{hydrostatic}- \rho g \Delta h


**Pump power**

Der Massenstrom wird durch die Druckdifferenz erzeugt, die von den Pumpen aufrecht erhalten wird.
Diese müssen den Druckabfall in den Rohren überwinden. Die Pumpleistung hängt dabei von
Druckverlusten
:math:`\Delta p` und Massenstrom :math:`\dot{m}` sowie der Effizienz (:math:`\eta_{pump} = \eta_{el} \cdot \eta_{hyd}`) der Pumpe ab.

.. math::
    P_{el. pump} = \frac{1}{\eta_{el}\eta_{hyd}}\frac{\Delta p }{\rho} \dot{m}


Da die Druckverluste selbst eine Funktion des Massenstroms :math:`\dot{m}` sind, enthält die
Pumpleistung einen Term dritter Ordnung in :math:`\dot{m}` und hängt damit nichtlinear vom
Massenstrom ab.


Thermal equations
~~~~~~~~~~~~~~~~~

Die Temperaturspreizung bestimmt die transportierte Wärmemenge:

.. math::
    \dot{Q} = \dot{m} \cdot c \cdot \Delta T.


Eine höhere Spreizung ermöglicht kleinere Rohrdurchmesser und damit geringere Kapitalkosten im Falle
einer Neuinstallation oder eine höhere Anschlussleistung für ein gegebenes Netz.

subsection{Wärmeverluste}
Die Wärmeverluste sind abhängig vom Temperaturniveau, der Strömungsgeschwindigkeit und der
Rohrdämmung.
Insbesondere die Darstellung der Wärmeverluste hängt stark vom Detailgrad ab. Im Folgenden wird
auf den stationären Zustand eingegangen. Die Temperatur am Ausgang des Rohres lässt sich in diesem
Fall wie folgt beschreiben \citep{Bohm2002}:

.. math::
    T_{out} = T_{env} + (T_{in} - T_{env}) \cdot exp\{-\frac{U \pi D L}{c \dot{m}}\}.


Wobei :math_`T_{in}` und :math_`T_{out}` die Temperaturen am Ein- und Ausgang des Rohres sind,
:math:`T_{env}` die Umgebungstemperatur und :math:`U` Wärmedurchgangskoeffizient. In Produktblättern
für Fernwärmeleitungen ist meist der spezifische Wärmeverlust pro Trassenmeter
:math:`U_{spez} [W/(K m)]` angegeben.

.. math::
    U_{spez} = U \cdot \pi D &\text{\hspace{1cm} for single pipes}\\
    U_{spez} = U \cdot 2 \pi D &\text{\hspace{1cm} for double pipes}




References
----------


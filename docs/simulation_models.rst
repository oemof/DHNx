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




References
----------


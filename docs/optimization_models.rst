.. _optimization_models_label:

~~~~~~~~~~~~~~~~~~~
Optimization models
~~~~~~~~~~~~~~~~~~~

Generally, this library should allow the optimization of district heating grids
with various configurations settings and different approaches.
The optimization methods of this library are tools to assist the
planning process of DHS projects and to analyze the economic feasibility of DHS
for a given district, community or city - either by focusing on the DHS itself,
or by also considering the overall energy system of a district, which could not
just be the heating sector, but also the electricity, mobility sector or the
gas infrastructure.

At the moment, there is one approach in this context implemented. This approach
is explained in the following sections.

Scope
-----

The following questions can be addressed using the `optimize_investment` method
of the *ThermalNetwork*:

* What is the cost-optimal topology and dimensioning of a DHS piping system?
  (Given the locations of potential central heat supply plants, the potential
  locations for the DHS piping system (e.g. street network),
  and the position of consumers)
* In addition to the first question, what is the cost-optimal expansion
  of a given DHS system.
* Is it cost-efficient to build a DHS at all, if there a consumer-wise heat
  supply alternatives? (Comparison of central and de-central supply strategies)
* What is the optimal dispatch of the heat producers? (Case, if there are no
  expansion options, but just existing DHS pipes)
* Planned: Streets-wise aggregation option

To answer these questions, at the moment,
the LP and MILP optimization library oemof.solph is used.
Other approaches, e.g. heuristic approaches, might follow.

The following sections will give an overview about the general usage/workflow,
(the necessary input data, the different optimization settings and options,
the results), and second, the underlying mathematical description.

Usage
-----

Links to the subsections:

* :ref:`Overview`
* :ref:`Input Data`
* :ref:`Optimization settings`
* :ref:`Results`

.. _Overview:

Overview
~~~~~~~~

The optimization of a given *ThermalNetwork* is executed by:

.. code-block:: python

    import dhnx

    tnw = dhnx.network.ThermalNetwork()

    tnw.optimize_investment(settings=set, invest_options=invest_opt)

For executing an optimization, you must provide the optimization `settings`
and the `invest_options` additional to the previous data, which defines a
*ThermalNetwork*.

.. _Input Data:

Input Data
~~~~~~~~~~

In this section, it is firstly revised, what input data is exactly necessary
from the *ThemalNetwork* class, and then explained, what data needs to be
provided as `invest_options` and as `settings`.

The following figure provides an overview of the input data:

.. 	figure:: _static/optimization_input_data.svg
   :width: 100 %
   :alt: optimization_input_data.svg
   :align: left

   Fig. 1: Optimization Input Data


ThermalNetwork
""""""""""""""

The data for the *ThermalNetwork* must be provided in the structure as defined
for the .csv reader. The following data is required for applying an
optimization:

.. code-block:: txt

    tree
    ├── edges.csv
    ├── consumers.csv
    ├── forks.csv
    ├── producers.csv
    └── sequences
        └── consumers-heat_flow.csv

The attributes, which are required, and which are optional with respect
to the optimization, are presented in detail in the following:

Edges
'''''

.. csv-table::
   :header-rows: 1
   :file: _static/opti_edges.csv

The following optional attributes are introduced by the optimization module:

* **existing**: Binary indicating an existing pipe. If there is no column
  *existing* given, all Edges are free for optimization.
* **capacity**: Capacity of existing pipes.
  If *existing* is *True*, a *capacity* must be given.
* **pipe_type**: Label of a type of pipe. The *pipe_type* refers to
  a set of parameters of a pipeline component. The parameters for a *pipe_type*
  must be given in the following table (see `pipe_options`).
  If *existing* is *True*, a *pipe_type* must be given.
* **active**: Binary indicating that this edge is considered. If no column
  *active* is given, all edges are active. With this attribute, single edges
  can be switched on and off. This can be very useful, if different scenarios
  should be analyzed, e.g. you might not know in advance, whether you are
  allowed to cross a property or use a street. (*not implemented yet*)
* **add_fix_costs**: Additional fix investment costs. Depending on the street
  and route of a DHS, the construction costs might differ. With this parameter,
  additional fix investment costs (independent of the size of the pipes) can be
  considered for each edge individually. Therefore, you need to apply a
  nonconvex investment (see `pipe_options`). (*not implemented yet*)

Consumers
'''''''''

.. csv-table::
   :header-rows: 1
   :file: _static/opti_consumers.csv

Producers
'''''''''

.. csv-table::
   :header-rows: 1
   :file: _static/opti_producers.csv

Forks
''''''

.. csv-table::
   :header-rows: 1
   :file: _static/opti_forks.csv

Consumers-heat_flow
'''''''''''''''''''



Investment Options
""""""""""""""""""

Text.

.. _Optimization settings:

Optimization settings
~~~~~~~~~~~~~~~~~~~~~

Text.

.. _Results:

Results
~~~~~~~

Text.


Underlying Concept
------------------

Text.

Thermal equations
~~~~~~~~~~~~~~~~~

Text.

Costs
~~~~~

Text.


References
----------

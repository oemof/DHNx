.. _thermal_network_label:

~~~~~~~~~~~~~~~
Thermal Network
~~~~~~~~~~~~~~~

The thermal network is the central object in DHNx. It provides a container class that holds
a number of components. All available components are defined in
`components.csv <https://github.com/oemof/DHNx/blob/dev/dhnx/components.csv>`_, which is
rendered in the following table.

.. csv-table::
   :header-rows: 1
   :file: ../dhnx/components.csv

Every component has a number of attributes which are defined in
`components_attrs/ <https://github.com/oemof/DHNx/blob/dev/dhnx/component_attrs>`_.
Each attribute is given a name, type (:attr:`int`, :attr:`float`, :attr:`str` etc.), unit,
default value, a description, a status (:attr:`Input` or :attr:`Output`) and requirement
(:attr:`required` or :attr:`optional`).

The attributes are presented in detail in the following sections.

Consumer
========

Consumers are the nodes where the heat provided by the district heating network is actually used.
They are characterized by these attributes:

.. csv-table::
   :header-rows: 1
   :file: ../dhnx/component_attrs/consumers.csv


Producer
========

A producer is a general node that provides heat to the district heating network.
Producers are described with the following attributes:

.. csv-table::
   :header-rows: 1
   :file: ../dhnx/component_attrs/producers.csv


Fork
====

Forks are the nodes where several edges of the network meet.
Forks have the attributes described in the following table:

.. csv-table::
   :header-rows: 1
   :file: ../dhnx/component_attrs/forks.csv


Edge
====

Edges represent the feed and return pipes connecting the different nodes of the network.
They are characterized by these attributes:

.. csv-table::
   :header-rows: 1
   :file: ../dhnx/component_attrs/edges.csv
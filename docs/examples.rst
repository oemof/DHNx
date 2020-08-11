.. _examples_label:

~~~~~~~~
Examples
~~~~~~~~

Create a thermal network
------------------------

.. code-block:: python

    from dhnx.network import ThermalNetwork

    thermal_network = ThermalNetwork()

    thermal_network.add('Producer', id=0, lat=50, lon=10)

    thermal_network.add('Consumer', id=0, lat=50, lon=10)

    thermal_network.add('Edge', id=0, from_node='producer-0', to_node='consumer-0')

    print(thermal_network)

    # returns
    # dhnx.network.ThermalNetwork object with these components
    #  * 1 producers
    #  * 1 consumers
    #  * 1 edges

    print(thermal_network.components.edges)

    # returns
    #        from_node     to_node
    #    0  producer-0  consumer-0


# -*- coding: utf-8

"""
This module is designed to hold optimization model implementations. The
implementation makes use of oemof-solph.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""


import oemof.solph as solph

import dhnx.optimization_add_components as ac
import dhnx.optimization_oemof_heatpipe as oh


def add_nodes_dhs(opti_network, gd, nodes, busd):
    """
    Based on the *forks* and *pipes* of the *ThermalNetwork* of the
    *OemofInvestOptimisationModel*, the oemof-solph components for the district heating
    network optimisation are initialised.

    For all *forks*, a `solph.Bus` with the label `infrastructure_heat_bus_forks-<id>`
    (string representation) is generated.

    For all *pipes*, a 'HeatPipeline' with the label
    `infrastructure_heat_<type>_<from_node>-<to_node>` (string representation)
    is generated. Depending on the attributes in *pipes*,
    an investment pipe, or an existing pipe is built.


    Parameters
    ----------
    opti_network : OemofInvestOptimisationModel
    gd : dict
        General optimisation settings.
    nodes : list
        List for collecting all oemof-solph objects.
    busd : dict
        Dictionary collecting all oemof-solph Buses. Keys: labels of the oemof-solph Buses;
        Values: oemof-solph Buses.

    Returns
    -------
    list, dict : List of all oemof-solph objects and dictionary of oemof-solph Buses.
    """

    d_labels = {}

    d_labels['l_2'] = 'heat'
    d_labels['l_3'] = 'bus'

    for n, _ in opti_network.thermal_network.components['forks'].iterrows():
        d_labels['l_4'] = 'forks-' + str(n)
        d_labels['l_1'] = 'infrastructure'
        l_bus = oh.Label(d_labels['l_1'], d_labels['l_2'], d_labels['l_3'],
                         d_labels['l_4'])
        bus = solph.Bus(label=l_bus)
        nodes.append(bus)
        busd[l_bus] = bus

    # add heatpipes for all lines
    for p, q in opti_network.thermal_network.components['pipes'].iterrows():

        pipe_data = opti_network.invest_options['network']['pipes']

        d_labels['l_1'] = 'infrastructure'
        d_labels['l_2'] = 'heat'

        if q['existing']:

            # terminate the first label
            l_1_in = 'infrastructure'
            l_1_out = 'infrastructure'

            typ_from = q['from_node'].split('-')[0]
            typ_to = q['to_node'].split('-')[0]

            if (typ_from == 'forks') and (typ_to == 'consumers'):
                l_1_out = 'consumers'

                start = q['from_node']
                end = q['to_node']
                b_in = busd[(l_1_in, d_labels['l_2'], 'bus', start)]
                b_out = busd[(l_1_out, d_labels['l_2'], 'bus', end)]
                d_labels['l_4'] = start + '-' + end
                nodes = ac.add_heatpipes_exist(pipe_data, d_labels, gd, q, b_in, b_out,
                                               nodes)

            elif (typ_from == 'consumers') and (typ_to == 'forks'):
                raise ValueError(
                    "Pipes must not go from 'consumers' to 'forks'!"
                    " Existing heatpipe id {}".format(p))

            elif (typ_from == 'forks') and (typ_to == 'producers'):
                l_1_in = 'producers'

                start = q['to_node']
                end = q['from_node']
                b_in = busd[(l_1_in, d_labels['l_2'], 'bus', start)]
                b_out = busd[(l_1_out, d_labels['l_2'], 'bus', end)]
                d_labels['l_4'] = start + '-' + end
                nodes = ac.add_heatpipes_exist(pipe_data, d_labels, gd, q,
                                               b_in, b_out,
                                               nodes)

            elif (typ_from == 'producers') and (typ_to == 'forks'):
                l_1_in = 'producers'

                start = q['from_node']
                end = q['to_node']
                b_in = busd[(l_1_in, d_labels['l_2'], 'bus', start)]
                b_out = busd[(l_1_out, d_labels['l_2'], 'bus', end)]
                d_labels['l_4'] = start + '-' + end
                nodes = ac.add_heatpipes_exist(pipe_data, d_labels, gd, q, b_in, b_out,
                                               nodes)

            elif (typ_from == 'forks') and (typ_to == 'forks'):

                start = q['from_node']
                end = q['to_node']
                b_in = busd[(l_1_in, d_labels['l_2'], 'bus', start)]
                b_out = busd[(l_1_out, d_labels['l_2'], 'bus', end)]
                d_labels['l_4'] = start + '-' + end
                nodes = ac.add_heatpipes_exist(pipe_data, d_labels, gd, q, b_in, b_out,
                                               nodes)

            else:
                raise ValueError("Something wrong!")

        else:   # calls Investment heatpipeline function
            # connection of houses
            if q['to_node'].split('-')[0] == "consumers":

                start = q['from_node']
                end = q['to_node']
                b_in = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', start)]
                b_out = busd[('consumers', d_labels['l_2'], 'bus', end)]

                d_labels['l_4'] = start + '-' + end

                nodes = ac.add_heatpipes(
                    pipe_data, d_labels, False, q['length'], b_in, b_out,
                    nodes)

            elif q['from_node'].split('-')[0] == "consumers":
                raise ValueError(
                    "Pipes must not go from 'consumers'!"
                    " Existing heatpipe id {}".format(p))

            elif q['to_node'].split('-')[0] == "producers":

                start = q['to_node']
                end = q['from_node']
                b_in = busd[('producers', d_labels['l_2'], 'bus', start)]
                b_out = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', end)]

                d_labels['l_4'] = start + '-' + end

                nodes = ac.add_heatpipes(
                    pipe_data, d_labels,
                    gd['bidirectional_pipes'], q['length'], b_in, b_out,
                    nodes)

            elif q['from_node'].split('-')[0] == "producers":

                start = q['from_node']
                end = q['to_node']
                b_in = busd[('producers', d_labels['l_2'], 'bus', start)]
                b_out = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', end)]

                d_labels['l_4'] = start + '-' + end

                nodes = ac.add_heatpipes(
                    pipe_data, d_labels, gd['bidirectional_pipes'], q['length'],
                    b_in, b_out, nodes,
                )

            elif (q['from_node'].split('-')[0] == 'forks') and (
                    q['to_node'].split('-')[0] == 'forks'):

                b_in = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', q['from_node'])]
                b_out = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', q['to_node'])]
                d_labels['l_4'] = q['from_node'] + '-' + q['to_node']

                nodes = ac.add_heatpipes(
                    pipe_data, d_labels, gd['bidirectional_pipes'], q['length'], b_in, b_out, nodes)

                if not gd['bidirectional_pipes']:
                    # the heatpipes from fork to fork need to be created in
                    # both directions in this case bidiretional = False
                    b_in = busd[(
                        d_labels['l_1'], d_labels['l_2'], 'bus', q['to_node'])]
                    b_out = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', q['from_node'])]
                    d_labels['l_4'] = q['to_node'] + '-' + q['from_node']

                    nodes = ac.add_heatpipes(
                        pipe_data, d_labels, gd['bidirectional_pipes'], q['length'], b_in, b_out,
                        nodes
                    )

            else:
                raise ValueError("Something wrong!")

    return nodes, busd


def add_nodes_houses(opti_network, nodes, busd, label_1):
    """
    For each *consumers*/*producers* of the *ThermalNetwork* of the
    *OemofInvestOptimisationModel*, the oemof-solph components for the *consumers*/*producers*
    are initialised depending on the given tables of the ``invest_options`` of the
    *OemofInvestOptimisationModel*.

    The tables of `invest_options` provide the information and attributes for the oemof-solph
    components, which should be build at every *consumer*/*producer*.

    The minimum requirement is to provide table with at least one *heat Bus* for all consumers
    and all producers, a table with a *heat sink* as demand for all consumers, and
    a table with at least one *heat source* for all producers.

    Additionally, further tables with *Transformer*, *Storages*, and further *Sources* and
    *Sinks* can be added.

    For the attributes for each table, you need to provide, please see:

    .. py:module::`~dhnx.optimization_modules.add_components`

    Parameters
    ----------
    opti_network : OemofInvestOptimisationModel

    gd : dict
        General optimisation settings.
    nodes : list
        List for collecting all oemof-solph objects.
    busd : dict
        Dictionary collecting all oemof-solph Buses. Keys: labels of the oemof-solph Buses;
        Values: oemof-solph Buses.
    label_1 : str
        First tag of the label, which is either `producers` or `consumers`.

    Returns
    -------
    list, dict : List of all oemof-solph objects and dictionary of oemof-solph Buses.

    """

    gen_data = opti_network.invest_options[label_1]     # genic data for all houses
    series = opti_network.thermal_network.sequences[label_1]    # sequences
    d_labels = {}

    for r, c in opti_network.thermal_network.components[label_1].iterrows():

        # heat bus is always necessary
        d_labels['l_1'] = label_1
        d_labels['l_4'] = label_1 + '-' + str(r)

        # add buses first, because other classes need to have them already
        nodes, busd = ac.add_buses(gen_data['bus'],
                                   d_labels, nodes, busd)

        for key, item in gen_data.items():

            if key == 'source':
                nodes = ac.add_sources(opti_network, item, c, d_labels, nodes, busd)

            if key == 'demand':
                nodes = ac.add_demand(item, d_labels, series, nodes, busd)

            if key == 'transformer':
                nodes = ac.add_transformer(item, d_labels, nodes, busd)

            if key == 'storages':
                nodes = ac.add_storage(item, d_labels, nodes, busd)

    return nodes, busd

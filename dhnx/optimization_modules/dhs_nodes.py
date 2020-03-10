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
from dhnx.optimization_modules import oemof_heatpipe as oh, add_components as ac


# def add_nodes_dhs(geo_data, gd, gd_infra, nodes, busd):
def add_nodes_dhs(opti_network, gd, nodes, busd):
    """
    :param geo_data: geometry data (points and line layer from qgis)
    :param gd: general data
    :param gd_infra: general data for infrastructure nodes
    :param nodes: list of nodes for oemof
    :param busd: dict of buses for building nodes
    :return:    nodes - updated list of nodes
                busd - updated list of buses
    """

    d_labels = {}

    d_labels['l_2'] = 'heat'
    d_labels['l_3'] = 'bus'

    # add heat buses for all nodes
    for n, o in opti_network.network.components['consumers'].iterrows():
        d_labels['l_4'] = 'consumers-' + str(n)
        d_labels['l_1'] = 'consumers'
        l_bus = oh.Label(d_labels['l_1'], d_labels['l_2'], d_labels['l_3'],
                         d_labels['l_4'])
        bus = solph.Bus(label=l_bus)
        nodes.append(bus)
        busd[l_bus] = bus

    for n, o in opti_network.network.components['forks'].iterrows():
        d_labels['l_4'] = 'forks-' + str(n)
        d_labels['l_1'] = 'infrastructure'
        l_bus = oh.Label(d_labels['l_1'], d_labels['l_2'], d_labels['l_3'],
                         d_labels['l_4'])
        bus = solph.Bus(label=l_bus)
        nodes.append(bus)
        busd[l_bus] = bus

    for n, o in opti_network.network.components['producers'].iterrows():
        d_labels['l_4'] = 'producers-' + str(n)
        d_labels['l_1'] = 'producers'
        l_bus = oh.Label(d_labels['l_1'], d_labels['l_2'], d_labels['l_3'],
                         d_labels['l_4'])
        bus = solph.Bus(label=l_bus)
        nodes.append(bus)
        busd[l_bus] = bus

    # add heatpipes for all lines
    for p, q in opti_network.network.components['edges'].iterrows():

        d_labels['l_1'] = 'infrastructure'
        d_labels['l_2'] = 'heat'

        # connection of houses
        if q['to_node'].split('-')[0] == "consumers":

            start = q['from_node']
            end = q['to_node']
            b_in = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', start)]
            b_out = busd[('consumers', d_labels['l_2'], 'bus', end)]

            d_labels['l_4'] = start + '-' + end

            nodes, busd = ac.add_heatpipes(
                opti_network.network.invest_options['network']['pipes'], d_labels, gd, q, b_in, b_out,
                nodes, busd)

        # connection energy generation site
        elif q['from_node'].split('-')[0] == "producers":

            start = q['from_node']
            end = q['to_node']
            b_in = busd[('producers', d_labels['l_2'], 'bus', start)]
            b_out = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', end)]

            d_labels['l_4'] = start + '-' + end

            nodes, busd = ac.add_heatpipes(
                opti_network.network.invest_options['network']['pipes'], d_labels, gd, q, b_in, b_out,
                nodes, busd)

        # connection of knots with 2 pipes in each direction since flow
        # direction is unknown
        if (q['from_node'].split('-')[0] =='forks') and (q['to_node'].split('-')[0] == 'forks'):

            start = q['from_node']
            end = q['to_node']
            b_in = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', start)]
            b_out = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', end)]

            d_labels['l_4'] = start + '-' + end

            nodes, busd = ac.add_heatpipes(
                opti_network.network.invest_options['network']['pipes'], d_labels, gd, q, b_in, b_out,
                nodes, busd)

            start = q['to_node']
            end = q['from_node']
            b_in = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', start)]
            b_out = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', end)]

            d_labels['l_4'] = start + '-' + end

            nodes, busd = ac.add_heatpipes(
                opti_network.network.invest_options['network']['pipes'], d_labels, gd, q, b_in, b_out,
                nodes, busd)

    return nodes, busd


def add_nodes_houses(opti_network, gd, nodes, busd, label_1):

    gen_data = opti_network.network.invest_options[label_1]  # genic data for all houses
    series = opti_network.network.sequences[label_1]        # sequences
    d_labels = {}

    for r, c in opti_network.network.components[label_1].iterrows():

        d_labels['l_1'] = label_1
        d_labels['l_4'] = label_1 + '-' + str(r)

        # add buses first, because other classes need to have them already
        nodes, busd = ac.add_buses(gen_data['bus'],
                                   d_labels, nodes, busd)

        for key, item in gen_data.items():

            # if key == 'bus':
            #     nodes, busd = ac.add_buses(item, d_labels, nodes, busd)

            if key == 'source':
                nodes, busd = ac.add_sources(item, d_labels, gd, nodes, busd)

            if key == 'demand':
                nodes, busd = ac.add_demand(item, d_labels, gd, series, nodes,
                                            busd)

            if key == 'transformer':
                nodes, busd = ac.add_transformer(item, d_labels, gd, nodes,
                                                 busd)

            if key == 'storages':
                nodes, busd = ac.add_storage(item, d_labels, gd, nodes, busd)

    return nodes, busd

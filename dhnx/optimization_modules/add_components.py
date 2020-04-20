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
from oemof.tools import economics
from dhnx.optimization_modules import oemof_heatpipe as oh
from dhnx.optimization_modules import auxiliary as aux


def add_buses(it, labels, nodes, busd):
    """
    :param it:  pd.Dataframe containing tabular information for the creation of
                buses
    :param labels: dict of label strings
    :return:
    """

    for i, b in it.iterrows():

        labels['l_3'] = 'bus'

        if b['active']:
            labels['l_2'] = b['label_2']
            l_bus = oh.Label(labels['l_1'], labels['l_2'], labels['l_3'],
                          labels['l_4'])

            # check if bus already exists (due to infrastructure)
            if l_bus in busd:
                print('bus bereits vorhanden:', l_bus)

            else:
                bus = solph.Bus(label=l_bus)
                nodes.append(bus)

                busd[l_bus] = bus

                if b['excess']:
                    labels['l_3'] = 'excess'
                    nodes.append(
                        solph.Sink(label=oh.Label(labels['l_1'], labels['l_2'],
                                               labels['l_3'], labels['l_4']),
                                   inputs={busd[l_bus]: solph.Flow(
                                       variable_costs=b['excess costs'])}))

                if b['shortage']:
                    labels['l_3'] = 'shortage'
                    nodes.append(
                        solph.Source(label=oh.Label(labels['l_1'], labels['l_2'],
                                                 labels['l_3'], labels['l_4']),
                                     outputs={busd[l_bus]: solph.Flow(
                                         variable_costs=b['shortage costs'])}))

    return nodes, busd


def add_sources(on, it, labels, gd, nodes, busd):

    # check if timeseries are given
    ts_status = False   # status if timeseries for sources is present
    if 'source_' + 'timeseries' in on.invest_options[labels['l_1']].keys():
        ts = on.invest_options[labels['l_1']]['source_' + 'timeseries']
        ts_status = True

    # check what flow attributes are given by what comes after 'active'
    flow_attr = list(it.columns)[2:]
    idx = flow_attr.index('active')
    flow_attr = flow_attr[idx+1:]

    for i, cs in it.iterrows():
        labels['l_3'] = 'source'

        if cs['active']:
            labels['l_2'] = cs['label_2']
            outflow_args = {}

            for fa in flow_attr:
                outflow_args[fa] = cs[fa]

            # add timeseries data if present
            if ts_status:
                ts_key = labels['l_4'].split('-')[1] + '_' + labels['l_2']
                for col in ts.columns.values:
                    if col.split('.')[0] == ts_key:
                        outflow_args[col.split('.')[1]] = ts[col].values

            nodes.append(
                solph.Source(
                    label=oh.Label(labels['l_1'], labels['l_2'],
                                     labels['l_3'], labels['l_4']),
                    outputs={busd[(
                        labels['l_1'], cs['label_2'], 'bus',
                        labels['l_4'])]: solph.Flow(**outflow_args)}))

    return nodes, busd


def add_demand(it, labels, gd, series, nodes, busd):

    for i, de in it.iterrows():
        labels['l_3'] = 'demand'

        if de['active']:
            labels['l_2'] = de['label_2']
            # set static inflow values
            inflow_args = {'nominal_value': de['scalingfactor'],
                           'fixed': de['fixed'],
                           'actual_value': series['heat_flow'][
                               int(labels['l_4'].split('-')[1])].values}

            # create
            nodes.append(
                solph.Sink(label=oh.Label(labels['l_1'], labels['l_2'],
                                       labels['l_3'], labels['l_4']),
                           inputs={
                               busd[(labels['l_1'], labels['l_2'], 'bus',
                                     labels['l_4'])]: solph.Flow(
                                        **inflow_args)}))

    return nodes, busd


def add_transformer(it, labels, gd, nodes, busd):

    for i, t in it.iterrows():
        labels['l_2'] = None

        if t['active']:
            labels['l_3'] = t['label_3']

            # Transformer with 1 Input and 1 Output
            if t['type'] == "1-in_1-out":

                b_in_1 = busd[(labels['l_1'], t['in_1'], 'bus', labels['l_4'])]
                b_out_1 = busd[(labels['l_1'], t['out_1'], 'bus',
                                labels['l_4'])]

                if t['invest']:

                    if t['eff_out_1'] == 'series':
                        print('noch nicht angepasst!')

                    # calculation epc
                    if t['annuity']:
                        epc_t = economics.annuity(
                            capex=t['capex'], n=t['n'], wacc=gd['rate']) \
                                * gd['f_invest']
                    else:
                        epc_t = t['capex']

                    # create
                    nodes.append(
                        solph.Transformer(
                            label=oh.Label(labels['l_1'], labels['l_2'],
                                        labels['l_3'], labels['l_4']),
                            inputs={b_in_1: solph.Flow()},
                            outputs={b_out_1: solph.Flow(
                                variable_costs=t['variable_costs'],
                                summed_max=t['in_1_sum_max'],
                                investment=solph.Investment(
                                    ep_costs=epc_t +
                                             t['service'] * gd['f_invest'],
                                    maximum=t['max_invest'],
                                    minimum=t['min_invest']))},
                            conversion_factors={
                                b_out_1: t['eff_out_1']}))

                else:
                    # create
                    if t['eff_out_1'] == 'series':
                        print('noch nicht angepasst!')
                        # for col in nd['timeseries'].columns.values:
                        #     if col.split('.')[0] == t['label']:
                        #         t[col.split('.')[1]] = nd['timeseries'][
                        #             col]

                    nodes.append(
                        solph.Transformer(
                            label=oh.Label(labels['l_1'], labels['l_2'],
                                        labels['l_3'], labels['l_4']),
                            inputs={b_in_1: solph.Flow()},
                            outputs={b_out_1: solph.Flow(
                                nominal_value=t['installed'],
                                summed_max=t['in_1_sum_max'],
                                variable_costs=t['variable_costs'])},
                            conversion_factors={b_out_1: t['eff_out_1']}))

    return nodes, busd


def add_storage(it, labels, gd, nodes, busd):

    for i, s in it.iterrows():
        if s['active']:

            label_storage = oh.Label(labels['l_1'], s['bus'], s['label'],
                                  labels['l_4'])
            label_bus = busd[(labels['l_1'], s['bus'], 'bus', labels['l_4'])]

            if s['invest']:

                if s['annuity']:
                    epc_s = economics.annuity(
                        capex=s['capex'], n=s['n'], wacc=gd['rate']) \
                            * gd['f_invest']
                else:
                    epc_s = s['capex']

                nodes.append(
                    solph.components.GenericStorage(
                        label=label_storage,
                        inputs={label_bus: solph.Flow()},
                        outputs={label_bus: solph.Flow()},
                        loss_rate=s['capacity_loss'],
                        invest_relation_input_capacity=s[
                            'invest_relation_input_capacity'],
                        invest_relation_output_capacity=s[
                            'invest_relation_output_capacity'],
                        inflow_conversion_factor=s['inflow_conversion_factor'],
                        outflow_conversion_factor=s[
                            'outflow_conversion_factor'],
                        investment=solph.Investment(ep_costs=epc_s)))

            else:
                nodes.append(
                    solph.components.GenericStorage(
                        label=label_storage,
                        inputs={label_bus: solph.Flow()},
                        outputs={label_bus: solph.Flow()},
                        loss_rate=s['capacity_loss'],
                        nominal_storage_capacity=s['capacity'],
                        inflow_conversion_factor=s['inflow_conversion_factor'],
                        outflow_conversion_factor=s[
                            'outflow_conversion_factor']))

    return nodes, busd


# when is this function still used? for old style like precalculation?
def add_heatpipes(it, labels, gd, q, b_in, b_out, nodes):

    for i, t in it.iterrows():

        if t['active']:

            # definition of tag3 of label -> type of pipe
            labels['l_3'] = t['label_3']

            epc_p, epc_fix = aux.precalc_cost_param(t, q, gd)

            # Heatpipe with binary variable
            nc = True if t['nonconvex'] else False

            # bidirectional heatpipelines yes or no
            flow_bi_args = {
                'bidirectional': True, 'min': -1}\
                if gd['bidirectional_pipes'] else {}

            nodes.append(oh.HeatPipeline(
                label=oh.Label(labels['l_1'], labels['l_2'],
                               labels['l_3'], labels['l_4']),
                inputs={b_in: solph.Flow(**flow_bi_args)},
                outputs={b_out: solph.Flow(
                    nominal_value=None,
                    **flow_bi_args,
                    investment=solph.Investment(
                        ep_costs=epc_p, maximum=t['cap_max'],
                        minimum=t['cap_min'], nonconvex=nc, offset=epc_fix,
                    ))},
                heat_loss_factor=t['l_factor']*q['length[m]'],
                heat_loss_factor_fix=t['l_factor_fix']*q['length[m]'],
            ))

    return nodes


def add_heatpipes_exist(pipes, labels, gd, q, b_in, b_out, nodes):

    # get index of existing pipe label of pipe data
    ind_pipe = pipes[pipes['label_3'] == q['hp_type']].index[0]

    hlf = pipes.at[ind_pipe, 'l_factor'] * q['length[m]']
    hlff = pipes.at[ind_pipe, 'l_factor_fix'] * q['length[m]']

    nodes.append(oh.HeatPipeline(
        label=oh.Label(labels['l_1'], labels['l_2'],
                       labels['l_3'], labels['l_4']),
        inputs={b_in: solph.Flow()},
        outputs={b_out: solph.Flow(
            nominal_value=q['capacity'])},
        heat_loss_factor=hlf,
        heat_loss_factor_fix=hlff,
    ))

    return nodes

# -*- coding: utf-8

"""
This module is designed to hold optimization model implementations. The
implementation makes use of oemof-solph.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

import os
from .model import OperationOptimizationModel, InvestOptimizationModel
from dhnx.optimization_modules.dhs_nodes import add_nodes_dhs,\
    add_nodes_houses, calc_consumer_connection
from dhnx.optimization_modules import oemof_heatpipe as oh, add_components as ac
from dhnx.optimization_modules import auxiliary as aux

import logging
import pandas as pd
import numpy as np

import oemof.solph as solph
from oemof.solph import helpers

class OemofOperationOptimizationModel(OperationOptimizationModel):
    r"""
    Implementation of an operation optimization model using oemof-solph.
    """
    def __init__(self, thermal_network):
        super().__init__(thermal_network)
        self.results = {}

    def setup(self):
        pass

    def solve(self):
        pass

    def get_results(self):
        return self.results


class OemofInvestOptimizationModel(InvestOptimizationModel):
    r"""
    Implementation of an invest optimization model using oemof-solph.
    """
    def __init__(self, thermal_network, settings, investment_options):
        self.settings = settings
        self.invest_options = investment_options
        super().__init__(thermal_network)
        self.results = {}

    def check_input(self):
        """This functions checks, if all there are any not-allowed edges. For
        the oemof optimization model, consumer-consumer, producer-producer, and
        diret producer-consumer connections are not allowed."""

        # check edges
        for p, q in self.network.components['edges'].iterrows():

            if (q['from_node'].split('-')[0] == "consumers") and (
                    q['to_node'].split('-')[0] == "consumers"):

                raise ValueError(
                    ""
                    "Edge id {} goes from consumer to consumer. This is not "
                    "allowed!".format(p))

            if (q['from_node'].split('-')[0] == "producers") and (
                    q['to_node'].split('-')[0] == "producers"):

                raise ValueError(
                    ""
                    "Edge id {} goes from producers to producers. "
                    "This is not allowed!".format(p))

            if ((q['from_node'].split('-')[0] == "producers") and (
                    q['to_node'].split('-')[0] == "consumers")) or ((
                    q['from_node'].split('-')[0] == "consumers") and (
                    q['to_node'].split('-')[0] == "producers")):

                raise ValueError(
                    ""
                    "Edge id {} goes from producers directly "
                    "to consumers, or vice versa. This is not allowed!"
                    "".format(p))

        # check sequences column index datatype
        # the columns must be integer
        if 'consumers' in self.network.sequences.keys():
            if self.network.sequences['consumers']['heat_flow'].columns.dtype != 'int64':
                self.network.sequences['consumers']['heat_flow'].columns = \
                    self.network.sequences['consumers']['heat_flow'].columns.\
                        astype('int64')

        return

    def precalc_consumers_connections(self):
        """This method pre calculates the house connections and adds the
        results to the edges as further input for the oemof solph model.
        This function should be used only, if all consumers should be
        connected to the dhs grid (not in case of central-decentral
        comparison).

        Notes:

            - if 'active' is not present in the edges tables, all consumers
            connections are pre-calculated.

            - as options for dimensioning, the same options for pipes should
            be used as for the optimization itself

            - as design power, either the max heat value of the consumers table
            is used (if 'max heat load' is given), or the maximum value of each
            timeseries is used (depending on the number of timesteps). This
            max heat value will be written in the consumers table.

            - the results of the precalculation should be written in the
            edges table, and should exactly look like as if existing pipes are
            given.

        """
        print('Info: Precalculation Consumers Connection')

        edges = self.network.components['edges']
        count = 0   # counts the number of pre-calculatet house connections
        count_multiple = 0 # counts the consumers, which have multiple connection options
        for r, c in self.network.components['consumers'].iterrows():

            # get edge index
            edge_id = edges[edges['to_node'] == 'consumers-' + str(r)].index

            if len(edge_id) > 1:
                count_multiple += 1
                print('consumers-{} has multiple options for connection to the grid.'
                      ''.format(str(r)))
                
            # only if there is just one option of connecting a consumer to the
            # grid, it makes sense to precalculate the house connection
            elif c['active'] and len(edge_id) == 1:

                house_connection = edges.T[edge_id[0]]
                # optimize single connection with oemof solph
                capacity, hp_typ = calc_consumer_connection(
                    house_connection, c['P_heat_max'], self.settings,
                    self.invest_options['network']['pipes'])                
                
                # put results into existing pipes data
                edges.at[edge_id, 'existing'] = 1
                edges.at[edge_id, 'capacity'] = capacity
                edges.at[edge_id, 'hp_type'] = hp_typ
                
                count += 1

            else:
                raise ValueError('Something wrong!')

        self.network.components['edges'] = edges

        num_active_consumers = \
            self.network.components['consumers']['active'].sum()
        
        print('Info: {} out of {} active consumers connections were precalculated.'
              ' {} consumers have multiple options for connecting to the grid.'.
              format(count, num_active_consumers, count_multiple))
        
        return

    def get_pipe_data(self):
        """Adds heat loss and investment costs (investment costs just for
        information) of all existing pipes to the edges table."""

        pipe_types = self.invest_options['network']['pipes'].copy()
        pipe_types.drop(pipe_types[pipe_types['active'] == 0].index,
                        inplace=True)
        edges = self.network.components['edges']

        # check if pipe type in pipe invest options
        hp_list = list(set(
            [x for x in edges['hp_type'].tolist()
             if isinstance(x, str)]))

        for hp in hp_list:
            if hp not in list(pipe_types['label_3']):
                raise ValueError(
                    "Existing heatpipe type {} is not in the list of "
                    "ACTIVE heatpipe investment options!".format(hp))

        def get_heat_loss(q):

            # get index of pipe datasheet
            ind = pipe_types[pipe_types['label_3'] == q['hp_type']].index

            t = pipe_types.loc[ind].squeeze()

            # differantiate between convex and nonconvex investments
            if t['nonconvex']:
                heat_loss = (t['l_factor'] * q['capacity'] +
                             t['l_factor_fix']) * q['length[m]']
            else:
                heat_loss = t['l_factor'] * q['capacity'] * q['length[m]']

            return heat_loss

        def get_invest_costs(opti_nw, q):

            # get index of pipe datasheet
            ind = pipe_types[pipe_types['label_3'] == c['hp_type']].index

            t = pipe_types.loc[ind].squeeze()
            gd = opti_nw.settings

            epc_p, epc_fix = aux.precalc_cost_param(t, q, gd)

            # differantiate between convex and nonconvex investments
            if t['nonconvex']:
                invest_costs = epc_p * q['capacity'] + epc_fix
            else:
                invest_costs = epc_p * q['capacity']

            return invest_costs

        # get investment costs
        for r, c in edges.iterrows():
            if isinstance(c['hp_type'], str):
                edges.at[r, 'heat_loss[kW]'] = get_heat_loss(c)
                edges.at[r, 'invest_costs[€]'] = get_invest_costs(self, c)
            else:
                edges.at[r, 'heat_loss[kW]'] = None
                edges.at[r, 'invest_costs[€]'] = None

        self.network.components['edges'] = edges

        return

    def setup_oemof_es(self):

        self.nodes = []  # list of all nodes
        self.buses = {}

        date_time_index = pd.date_range(self.settings['start_date'],
                                        periods=self.settings['num_ts'],
                                        freq=self.settings['frequence'])

        # logger.define_logging()
        logging.info('Initialize the energy system')

        self.es = solph.EnergySystem(timeindex=date_time_index)

        logging.info('Create oemof objects')

        # qgis_data : ursprünglich dict mit point and line layer
        # gd_infra : invest optionen heat pipe
        # data_houses : dict mit excel/csv (buses, transformer, ...) daten von consumer
        # data_generation : dict mit excel/csv (buses, transformer, ...) daten von generation/producer

        # add houses
        for typ in ['consumers', 'producers']:
            self.nodes, self.buses = add_nodes_houses(
                self, self.settings, self.nodes, self.buses, typ)

        logging.info('Producers, Consumers Nodes appended.')

        # add heating infrastructure
        self.nodes, self.buses = add_nodes_dhs(self, self.settings, self.nodes,
                                               self.buses)
        logging.info('DHS Nodes appended.')

        # add nodes and flows to energy system
        self.es.add(*self.nodes)

        logging.info('Energysystem has been created')
        print("*********************************************************")
        print("The following objects have been created:")
        for n in self.es.nodes:
            oobj = \
                str(type(n)).replace("<class 'oemof.solph.", "").replace("'>",
                                                                         "")
            print(oobj + ':', n.label)
        print("*********************************************************")

        return

    def setup(self):

        # initial check of edges connections
        self.check_input()

        # create edges attribute hp_type, if not in the table so far
        if 'hp_type' not in list(self.network.components['edges'].columns):
            self.network.components['edges']['hp_type'] = None

        # if there is no information about active edges, all edges are active
        if 'active' not in list(self.network.components['edges'].columns):
            self.network.components['edges']['active'] = 1

        # in case the attribute 'active' is not present, it is supposed
        # that all consumers are active
        if 'active' not in list(self.network.components['consumers'].index):
            self.network.components['consumers']['active'] = 1

        # prepare heat data, whether global simultanity or timeseries
        if 'P_heat_max' not in list(
                self.network.components['consumers'].columns):

            df_max = self.network.sequences['consumers']['heat_flow'].max().\
                to_frame(name='P_heat_max')

            # df_max.index = pd.Index([int(x) for x in list(df_max.index)])

            self.network.components['consumers'] = \
                pd.concat([self.network.components['consumers'], df_max],
                          axis=1, join='inner')

        # check, which optimization type should be performed
        if self.settings['heat_demand'] == 'scalar':
            # checks for single timestep optimisation

            # just single timestep optimization, overwrite previous!
            self.settings['num_ts'] = 1

            # new approach
            P_max = self.network.components['consumers']['P_heat_max']
            df_ts = pd.DataFrame(data=[P_max.values],
                                 columns=list(P_max.index),
                                 index=pd.Index([0], name='timestep'))

            # heat load is maximum heat load mutiplied with SF
            self.network.sequences['consumers']['heat_flow'] = \
                df_ts * self.settings['global_SF']

        if self.settings['num_ts'] > \
                len(self.network.sequences['consumers']['heat_flow'].index):

            raise ValueError(
                'The length of the heat demand timeseries is not sufficient '
                'for the given number of {} timesteps.'.format(
                    self.settings['num_ts']))

        # check whether there the 'existing' attribute is present at the edges
        if 'existing' not in self.network.components['edges'].columns:
            self.network.components['edges']['existing'] = 0

        # precalculate house connections if wanted
        # precalculates takes always the 'P_heat_max' of each house for
        # dimesioning, without simultaneity factor. The simultaneitgy factor
        # is applied to the timeseries, which are in case of single-timestep
        # optimisation inserted and replaced above
        if self.settings['precalc_consumer_connections']:
            # if self.settings['dhs'] != 'fix':
            #     raise ValueError(
            #         'Are you sure, you want to do that?! '
            #         'If you want to precalculate the consumers connections, '
            #         'set the optimisation setting option "dhs" to "fix"!')
            self.precalc_consumers_connections()

        # if there is the existing attribute, get the information about
        # the pipe types (like heat_loss)
        self.get_pipe_data()

        # set up oemof energy system
        self.setup_oemof_es()

        return

    def solve(self, solver='cbc', solve_kw=None):

        logging.info('Build the operational model')
        self.om = solph.Model(self.es)

        logging.info('Solve the optimization problem')
        self.om.solve(solver=self.settings['solver'],
                      solve_kwargs=self.settings['solve_kw'])

        filename = os.path.join(
            helpers.extend_basic_path('lp_files'), 'DHNx.lp')
        logging.info('Store lp-file in {0}.'.format(filename))
        self.om.write(filename, io_options={'symbolic_solver_labels': True})

        self.es.results['main'] = solph.processing.results(self.om)
        self.es.results['meta'] = solph.processing.meta_results(self.om)

        return

    def get_results_edges(self):

        def get_invest_val(lab):

            res = self.es.results['main']

            outflow = [x for x in res.keys()
                       if x[1] is not None
                       if lab == x[0].label.__str__()]

            if len(outflow) > 1:
                print('Multiple IDs!')

            try:
                invest = res[outflow[0]]['scalars']['invest']
            except:
                try:
                    # that's in case of a one timestep optimisation due to
                    # an oemof bug in outputlib
                    invest = res[outflow[0]]['sequences']['invest'][0]
                except:
                    # this is in case there is no bi-directional heatpipe, e.g. at
                    # forks-consumers, producers-forks
                    invest = 0

            return invest

        def get_hp_results():
            """The edge specific investment results of the heatpipelines are
            put
            """

            label_base = 'infrastructure_' + 'heat_' + hp + '_'

            # maybe slow approach with lambda function
            df[hp + '.' + 'dir-1'] = df['from_node'] + '-' + df['to_node']
            df[hp + '.' + 'size-1'] = df[hp + '.' + 'dir-1'].apply(
                lambda x: get_invest_val(label_base + x))
            df[hp + '.' + 'dir-2'] = df['to_node'] + '-' + df['from_node']
            df[hp + '.' + 'size-2'] = df[hp + '.' + 'dir-2'].apply(
                lambda x: get_invest_val(label_base + x))

            df[hp + '.' + 'size'] = \
                df[[hp + '.' + 'size-1', hp + '.' + 'size-2']].max(axis=1)

            return df

        def check_multi_dir_invest():

            df = self.network.components['edges']

            df_double_invest = \
                df[(df[hp + '.' + 'size-1'] > 0.001) & (df[hp + '.' + 'size-2'] > 0.001)]

            print('***')
            if df_double_invest.empty:
                print('There is NO investment in both directions at the'
                      'following edges for "', hp, '"')
            else:
                print('There is an investment in both directions at the'
                      'following edges for "', hp, '":')
                print('----------')
                print(' id | from_node | to_node | size-1 | size-2 ')
                print('============================================')
                for r, c in df_double_invest.iterrows():
                    print(r, ' | ', c['from_node'], ' | ', c['to_node'],
                          ' | ', c[hp + '.' + 'size-1'], ' | ', c[hp + '.' + 'size-2'], ' | ')
                print('----------')

            return

        # use edges dataframe as base and add results as new columns to it
        df = self.network.components['edges']

        # putting the results of the investments in heatpipes to the edges:
        df_hp = self.invest_options['network']['pipes']

        # list of active heat pipes
        active_hp = list(df_hp[df_hp['active'] == 1]['label_3'].values)

        for hp in active_hp:
            get_hp_results()
            check_multi_dir_invest()

        def write_results_to_edges():

            def check_invest_label():
                if isinstance(c['hp_type'], str):
                    raise ValueError(
                        "Edge id {} already has an investment > 0!".format(r))

            for hp in active_hp:
                for r, c in df.iterrows():
                    if c[hp + '.size'] > 0:
                        check_invest_label()
                        df.at[r, 'hp_type'] = hp
                        df.at[r, 'capacity'] = c[hp + '.size']

            return

        write_results_to_edges()

        self.get_pipe_data()

        return df


def optimize_operation(thermal_network):
    r"""
    Takes a thermal network and returns the result of
    the operational optimization.

    Parameters
    ----------
    thermal_network

    Returns
    -------
    results : dict
    """
    model = OemofOperationOptimizationModel(thermal_network)

    model.solve()

    results = model.get_results()

    return results


def optimize_investment(thermal_network, invest_options, settings=None):
    r"""
    Takes a thermal network and returns the result of
    the investment optimization.
    """
    setting_default = {
        'heat_demand': 'scalar',
        'num_ts': 1,
        'time_res': 1,
        'rate': 0.01,
        'f_invest': 1,
        'start_date': '1/1/2018',
        'frequence': 'H',
        'solver': 'cbc',
        'solve_kw': {'tee': False},
        'dhs': 'optional',
        'simultaneity': 'global',
        'global_SF': 1,
        'SF_timeseries': 1,
        'SF_1_timeseries': 1,
        'precalc_consumer_connections': False,
        'bidirectional_pipes': False,
    }

    if settings is not None:
        given_keys = [x for x in settings.keys()
                      if x in setting_default.keys()]

        for key in given_keys:
            setting_default[key] = settings[key]

    model = OemofInvestOptimizationModel(thermal_network, setting_default,
                                         invest_options)

    model.solve(solver=setting_default['solver'],
                solve_kw=setting_default['solve_kw'])

    edges_results = model.get_results_edges()

    results = {'oemof': model.es.results['main'],
               'oemof_meta': model.es.results['meta'],
               'components': {'edges': edges_results}}

    return results

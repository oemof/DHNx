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
from dhnx.optimization_modules.dhs_nodes import add_nodes_dhs, add_nodes_houses

import logging
import pandas as pd

import oemof.solph as solph
import oemof.outputlib as outputlib
from oemof.tools import helpers

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
        if self.network.sequences['consumers']['heat_flow'].columns.dtype != 'int64':
            self.network.sequences['consumers']['heat_flow'].columns = \
                self.network.sequences['consumers']['heat_flow'].columns.\
                    astype('int64')

        return

    def get_pipe_data_existing(self):
        """Adds heat loss and investment costs (investment costs just for
        information) of all existing pipes to the edges table."""

        pipe_types = self.invest_options['network']['pipes'].copy()
        pipe_types.drop(pipe_types[pipe_types['active'] == 0].index, inplace=True)
        edges = self.network.components['edges']

        # check if pipe type in pipe invest options
        hp_list = list(set(
            [x for x in edges['hp_type'].tolist() if str(x) != 'nan']))

        for hp in hp_list:
            if hp not in list(pipe_types['label_3']):
                raise ValueError(
                    "Existing heatpipe type {} is not in the list of "
                    "ACTIVE heatpipe investment options!".format(hp))

        def get_heat_loss(typ, capa):

            ind = pipe_types[pipe_types['label_3'] == typ].index
            heat_loss = pipe_types.loc[ind]['l_factor'].values[0] * capa + \
                        pipe_types.loc[ind]['l_factor_fix'].values[0]

            return heat_loss

        def get_invest_costs(typ, capa):

            ind = pipe_types[pipe_types['label_3'] == typ].index
            heat_loss = pipe_types.loc[ind]['capex_pipes'].values[0] * capa + \
                        pipe_types.loc[ind]['fix_costs'].values[0]

            return heat_loss

        edges['heat_loss[1/m]'] = edges.apply(
            lambda x: get_heat_loss(x['hp_type'], x['capacity'])
            if x['existing'] == 1 else None, axis=1)

        edges['invest_costs[€/m]'] = edges.apply(
            lambda x: get_invest_costs(x['hp_type'], x['capacity'])
            if x['existing'] == 1 else None, axis=1)

        self.network.components['edges'] = edges

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

        print('Precalculation Consumers Connection')

        # get max heat load
        # if ''


        for r, c in self.network.components['consumers'].iterrows():

            if 'active' not in list(c.index):
                c['active'] = 1

            # if c['active']:






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
        if self.settings['dhs'] == 'fix':

            # checks for single timestep optimisation

            # just single timestep optimization, overwrite previous!
            self.settings['num_ts'] = 1

            # heat load is maximum heat load mutiplied with SF
            seq = self.network.sequences['consumers']['heat_flow']
            seq.drop(seq.index[1:], inplace=True)
            seq_T = seq.T
            # seq_T.index = pd.Index([int(x) for x in list(seq_T.index)])
            seq_T = pd.concat([seq_T, self.network.components['consumers'][
                'P_heat_max']], axis=1, join='inner')
            seq_T[0] = seq_T['P_heat_max']
            seq_T.drop(['P_heat_max'], axis=1, inplace=True)
            self.network.sequences['consumers']['heat_flow'] = \
                seq_T.T * self.settings['global_SF']

        if self.settings['num_ts'] > \
                len(self.network.sequences['consumers']['heat_flow'].index):

            raise ValueError(
                'The length of the heat demand timeseries is not sufficient '
                'for the given number of {} timesteps.'.format(
                    self.settings['num_ts']))

        # check whether there are existing pipes in the network
        if 'existing' in self.network.components['edges'].columns:
            # if there is the existing attribute, get the information about
            # the pipe types (like heat_loss)
            self.get_pipe_data_existing()
        else:
            self.network.components['edges']['existing'] = 0

        # precalculate house connections if wanted
        # precalculates takes always the 'P_heat_max' of each house for
        # dimesioning, without simultaneity factor. The simultaneitgy factor
        # is applied to the timeseries, which are in case of single-timestep
        # optimisation inserted and replaced above
        precalc = False
        if precalc:
            self.precalc_consumers_connections()

        # set up oemof energy system
        self.setup_oemof_es()

        return

    def solve(self, solver='cbc', solve_kw=None):

        logging.info('Build the operational model')
        self.om = solph.Model(self.es)

        logging.info('Solve the optimization problem')
        self.om.solve(solver=self.settings['solver'],
                      solve_kwargs=self.settings['solve_kw'])

        self.es.results['main'] = outputlib.processing.results(self.om)
        # self.es.results['meta'] = outputlib.processing.meta_results(self.om)

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


def optimize_investment(thermal_network, settings, invest_options):
    r"""
    Takes a thermal network and returns the result of
    the investment optimization.

    Parameters
    ----------
    thermal_network

    Returns
    -------
    results : dict
    """
    model = OemofInvestOptimizationModel(thermal_network, settings,
                                         invest_options)

    model.solve(solver=settings['solver'], solve_kw=settings['solve_kw'])

    edges_results = model.get_results_edges()

    results = {'oemof': model.es.results['main'],
               'components': {'edges': edges_results}}

    return results

# -*- coding: utf-8

"""
This module is designed to hold optimization model implementations. The
implementation makes use of oemof-solph.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

from .model import OperationOptimizationModel, InvestOptimizationModel
from dhnx.optimization_modules.dhs_nodes import add_nodes_dhs, add_nodes_houses

import logging
import pandas as pd

import oemof.solph as solph
import oemof.outputlib as outputlib


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

    def setup(self):

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

            try:
                scalar = outputlib.views.node(res, lab)['scalars'][0]
            except:
                scalar = 0

            return scalar

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
                      'following edges for "', hp, '":')
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

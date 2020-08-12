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
import logging
import pandas as pd
import oemof.solph as solph
from oemof.solph import helpers

from .optimization_modules.dhs_nodes import add_nodes_dhs,\
    add_nodes_houses
from .optimization_modules import auxiliary as aux
from .model import OperationOptimizationModel, InvestOptimizationModel


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
        self.nodes = []  # list of all nodes
        self.buses = {}
        self.es = solph.EnergySystem()
        self.om = None

        # list of possible oemof flow attributes
        self.oemof_flow_attr = {'nominal_value', 'min', 'max',
                                'variable_costs', 'fix'}

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
            if self.network.sequences['consumers']['heat_flow'].columns.dtype \
                    != 'int64':
                self.network.sequences['consumers']['heat_flow'].columns = \
                    self.network.sequences['consumers']['heat_flow'].columns.astype('int64')

    def complete_exist_data(self):

        pipe_types = self.invest_options['network']['pipes']
        edges = self.network.components['edges']

        for r, c in edges.iterrows():
            if c['active']:
                if c['existing']:
                    idx = pipe_types[pipe_types['label_3'] == c['hp_type']].index[0]
                    if pipe_types.at[idx, 'nonconvex'] == 1:
                        if c['capacity'] > 0:
                            edges.at[r, 'invest_status'] = 1
                        elif c['capacity'] == 0:
                            edges.at[r, 'invest_status'] = 0
                        else:
                            print('Something wrong?!')
                    # else:
                    #     edges.at[r, 'invest_status'] = None

        self.network.components['edges'] = edges

    def get_pipe_data(self):
        """Adds heat loss and investment costs (investment costs just for
        information) of all existing pipes to the edges table."""

        pipe_types = self.invest_options['network']['pipes'].copy()
        pipe_types.drop(pipe_types[pipe_types['active'] == 0].index,
                        inplace=True)
        edges = self.network.components['edges']

        # just take active heatpipes
        edges_active = edges[edges['active'] == 1]

        # check if pipe type in pipe invest options
        hp_list = list({x for x in edges_active['hp_type'].tolist()
                        if isinstance(x, str)})

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
            if t['nonconvex'] is True:
                heat_loss = (t['l_factor'] * q['capacity'] + t['l_factor_fix'] * q[
                    'invest_status']) * q['length[m]']
            else:
                heat_loss = t['l_factor'] * q['capacity'] * q['length[m]'] + \
                    t['l_factor_fix'] * q['length[m]']

            return heat_loss

        def get_invest_costs(opti_nw, q):

            # get index of pipe datasheet
            ind = pipe_types[pipe_types['label_3'] == q['hp_type']].index

            t = pipe_types.loc[ind].squeeze()
            gd = opti_nw.settings

            epc_p, epc_fix = aux.precalc_cost_param(t, q, gd)

            # differantiate between convex and nonconvex investments
            if t['nonconvex']:
                invest_costs = epc_p * q['capacity'] + epc_fix * q['invest_status']
            else:
                invest_costs = epc_p * q['capacity']

            return invest_costs

        # get investment costs
        for r, c in edges_active.iterrows():
            if isinstance(c['hp_type'], str):
                edges.at[r, 'heat_loss[kW]'] = get_heat_loss(c)
                if 'annuity' in pipe_types.columns:
                    edges.at[r, 'invest_costs[€]'] = get_invest_costs(self, c)
                else:
                    edges.at[r, 'invest_costs[€]'] = None
            else:
                edges.at[r, 'heat_loss[kW]'] = None
                edges.at[r, 'invest_costs[€]'] = None

        self.network.components['edges'] = edges

    def setup_oemof_es(self):

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
        # data_generation :
        #       dict mit excel/csv (buses, transformer, ...) daten von generation/producer

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

        if self.settings['print_logging_info']:
            print("*********************************************************")
            print("The following objects have been created:")
            for n in self.es.nodes:
                oobj = \
                    str(type(n)).replace("<class 'oemof.solph.", "").replace("'>",
                                                                             "")
                print(oobj + ':', n.label)
            print("*********************************************************")

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

            self.network.components['consumers'] = \
                pd.concat([self.network.components['consumers'], df_max],
                          axis=1, join='inner')

        # check, which optimization type should be performed
        if self.settings['heat_demand'] == 'scalar':

            # just single timestep optimization, overwrite previous!
            self.settings['num_ts'] = 1

            # new approach
            p_max = self.network.components['consumers']['P_heat_max']
            df_ts = pd.DataFrame(data=[p_max.values],
                                 columns=list(p_max.index),
                                 index=pd.Index([0], name='timestep'))

            # heat load is maximum heat load mutiplied with simultaneity
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

        # get invest_status in order that .get_pipe_data() works proberly for
        # existing pipes - maybe, needs to be adapted in future
        self.complete_exist_data()

        # apply global simultaneity for demand series
        self.network.sequences['consumers']['heat_flow'] = \
            self.network.sequences['consumers']['heat_flow'] * \
            self.settings['global_SF']

        # if there is the existing attribute, get the information about
        # the pipe types (like heat_loss)
        self.get_pipe_data()

        # set up oemof energy system
        self.setup_oemof_es()

    def solve(self):

        logging.info('Build the operational model')
        self.om = solph.Model(self.es)

        logging.info('Solve the optimization problem')
        self.om.solve(solver=self.settings['solver'],
                      solve_kwargs=self.settings['solve_kw'])

        if self.settings['write_lp_file']:
            filename = os.path.join(
                helpers.extend_basic_path('lp_files'), 'DHNx.lp')
            logging.info('Store lp-file in %s', filename)
            self.om.write(filename, io_options={'symbolic_solver_labels': True})

        self.es.results['main'] = solph.processing.results(self.om)
        self.es.results['meta'] = solph.processing.meta_results(self.om)

    def get_results_edges(self):

        def get_invest_val(lab):

            res = self.es.results['main']

            outflow = [x for x in res.keys()
                       if x[1] is not None
                       if lab == x[0].label.__str__()]

            if len(outflow) > 1:
                print('Multiple IDs!')

            # invest = res[outflow[0]]['scalars']['invest']

            try:
                invest = res[outflow[0]]['scalars']['invest']
            except (KeyError, IndexError):
                try:
                    # that's in case of a one timestep optimisation due to
                    # an oemof bug in outputlib
                    invest = res[outflow[0]]['sequences']['invest'][0]
                except (KeyError, IndexError):
                    # this is in case there is no bi-directional heatpipe, e.g. at
                    # forks-consumers, producers-forks
                    invest = 0

            return invest

        def get_invest_status(lab):

            res = self.es.results['main']

            outflow = [x for x in res.keys()
                       if x[1] is not None
                       if lab == str(x[0].label)]

            try:
                invest_status = res[outflow[0]]['scalars']['invest_status']
            except (KeyError, IndexError):
                try:
                    # that's in case of a one timestep optimisation due to
                    # an oemof bug in outputlib
                    invest_status = res[outflow[0]]['sequences']['invest_status'][0]
                except (KeyError, IndexError):
                    # this is in case there is no bi-directional heatpipe, e.g. at
                    # forks-consumers, producers-forks
                    invest_status = 0

            return invest_status

        def get_hp_results(p):
            """The edge specific investment results of the heatpipelines are
            put
            """

            hp_lab = p['label_3']
            label_base = 'infrastructure_' + 'heat_' + hp_lab + '_'

            # maybe slow approach with lambda function
            df[hp_lab + '.' + 'dir-1'] = df['from_node'] + '-' + df['to_node']
            df[hp_lab + '.' + 'size-1'] = df[hp_lab + '.' + 'dir-1'].apply(
                lambda x: get_invest_val(label_base + x))
            df[hp_lab + '.' + 'dir-2'] = df['to_node'] + '-' + df['from_node']
            df[hp_lab + '.' + 'size-2'] = df[hp_lab + '.' + 'dir-2'].apply(
                lambda x: get_invest_val(label_base + x))

            df[hp_lab + '.' + 'size'] = \
                df[[hp_lab + '.' + 'size-1', hp_lab + '.' + 'size-2']].max(axis=1)

            if p['nonconvex']:
                df[hp_lab + '.' + 'status-1'] = df[hp_lab + '.' + 'dir-1'].apply(
                    lambda x: get_invest_status(label_base + x))
                df[hp_lab + '.' + 'status-2'] = df[hp_lab + '.' + 'dir-2'].apply(
                    lambda x: get_invest_status(label_base + x))
                df[hp_lab + '.' + 'status'] = \
                    df[[hp_lab + '.' + 'status-1', hp_lab + '.' + 'status-2']].max(axis=1)

            return df

        def check_multi_dir_invest(hp_lab):

            ed = self.network.components['edges']

            df_double_invest = \
                ed[(ed[hp_lab + '.' + 'size-1'] > 0.001) & (ed[hp_lab + '.' + 'size-2'] > 0.001)]

            if self.settings['print_logging_info']:
                print('***')
                if df_double_invest.empty:
                    print('There is NO investment in both directions at the'
                          'following edges for "', hp_lab, '"')
                else:
                    print('There is an investment in both directions at the'
                          'following edges for "', hp_lab, '":')
                    print('----------')
                    print(' id | from_node | to_node | size-1 | size-2 ')
                    print('============================================')
                    for r, c in df_double_invest.iterrows():
                        print(r, ' | ', c['from_node'], ' | ', c['to_node'],
                              ' | ', c[hp_lab + '.' + 'size-1'], ' | ',
                              c[hp_lab + '.' + 'size-2'], ' | ')
                    print('----------')

        # use edges dataframe as base and add results as new columns to it
        df = self.network.components['edges']

        # putting the results of the investments in heatpipes to the edges:
        df_hp = self.invest_options['network']['pipes']

        # list of active heat pipes
        active_hp = list(df_hp[df_hp['active'] == 1]['label_3'].values)

        for hp in active_hp:
            hp_param = df_hp[df_hp['label_3'] == hp].squeeze()
            get_hp_results(hp_param)
            check_multi_dir_invest(hp)

        def write_results_to_edges(pipe_data):

            def check_invest_label(hp_type, edge_id):
                if isinstance(hp_type, str):
                    raise ValueError(
                        "Edge id {} already has an investment > 0!".format(edge_id))

            for ahp in active_hp:
                p = pipe_data[pipe_data['label_3'] == ahp].squeeze()   # series of heatpipe
                for r, c in df.iterrows():
                    if c[ahp + '.size'] > 0:
                        check_invest_label(c['hp_type'], id)
                        df.at[r, 'hp_type'] = ahp
                        df.at[r, 'capacity'] = c[ahp + '.size']
                        if p['nonconvex']:
                            df.at[r, 'invest_status'] = c[ahp + '.status']
                        else:
                            df.at[r, 'invest_status'] = None

        write_results_to_edges(df_hp)

        self.get_pipe_data()

        return df


def optimize_operation(thermal_network):
    r"""
    Takes a thermal network and returns the result of
    the operational optimization.
    """
    model = OemofOperationOptimizationModel(thermal_network)

    model.solve()

    results = model.get_results()

    return results


def setup_optimise_investment(thermal_network, invest_options, settings=None):
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
        'dump_path': None,
        'dump_name': 'dump.oemof',
        'get_invest_results': True,
        'print_logging_info': False,
        'write_lp_file': False,
    }

    if settings is not None:
        given_keys = [x for x in settings.keys()
                      if x in setting_default.keys()]

        for key in given_keys:
            setting_default[key] = settings[key]

    model = OemofInvestOptimizationModel(thermal_network, setting_default,
                                         invest_options)

    return model


def solve_optimisation_investment(model):

    model.solve()

    if model.settings['dump_path'] is not None:
        my_es = model.es
        my_es.dump(dpath=model.settings['dump_path'], filename=model.settings['dump_name'])
        print('oemof Energysystem stored in "{}"'.format(model.settings['dump_path']))

    if model.settings['get_invest_results']:
        edges_results = model.get_results_edges()
    else:
        edges_results = model.network.components['edges']

    results = {'oemof': model.es.results['main'],
               'oemof_meta': model.es.results['meta'],
               'components': {'edges': edges_results}}

    return results

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
    """
    Implementation of an invest optimization model using oemof-solph.

    ...

    Attributes
    ----------
    settings : dict
        Dictionary holding the optimisation settings. See .
    invest_options : dict
        Dictionary holding the investment options for the district heating system.
    nodes : list
        Empty list for collecting all oemof.solph nodes.
    buses : dict
        Empty dictionary for collecting all oemof.solph.Buses of the energy system.
    es : oemof.solph.EnergySystem
        Empty oemof.solph.EnergySystem.
    om : oemof.solph.Model
        Attribute, which will be the oemof.solph.Model for optimisation.
    oemof_flow_attr : set
        Possible flow attributes, which can be used additionally:
        {'nominal_value', 'min', 'max', 'variable_costs', 'fix'}
    results : dict
        Empty dictionary for the results.

    Methods
    -------
    check_input():
        Performs checks on the input data.
    complete_exist_data():
        Sets the investment status for the results dataframe of the pipes.
    get_pipe_data():
        Adds heat loss and investment costs to pipes dataframe.
    setup_oemof_es():
        The energy system *es* is build.
    setup():
        Calls *check_input()*, *complete_exist_data()*, *get_pipe_data()*, and *setup_oemof_es()*.

    """
    def __init__(self, thermal_network, settings, investment_options):

        self.settings = settings
        self.invest_options = investment_options
        self.nodes = []  # list of all nodes
        self.buses = {}  # dict of all buses
        self.es = solph.EnergySystem()
        self.om = None

        # list of possible oemof flow attributes, e.g. for producers source
        self.oemof_flow_attr = {'nominal_value', 'min', 'max',
                                'variable_costs', 'fix'}

        super().__init__(thermal_network)
        self.results = {}

    def check_input(self):
        """Check 1:

        Check and make sure, that the dtypes of the columns of the sequences
        and the indices (=ids) of the forks, pipes, producers and consumers
        are of type 'str'. (They need to be the same dtye.)

        Check 2:

        Firstly, it is checked, if there are any not-allowed connection in the *pipe* data.
        The following connections are not allowed:

          * consumer -> consumer
          * producer -> producer
          * producer -> consumer
          * consumer -> fork

        Secondly, it is checked, if a pipes goes to a consumer, which does not exist.

        An error is raised if one of these connection occurs.
        """

        # Check 1
        # make sure that all ids are of type str
        # sequences
        sequ_items = self.network.sequences.keys()
        for it in sequ_items:
            for v in self.network.sequences[it].values():
                v.columns.astype('str')

        # components
        for comp in ['pipes', 'consumers', 'producers', 'forks']:
            self.network.components[comp].index = \
                self.network.components[comp].index.astype('str')

        # Check 2

        ids_consumers = self.network.components['consumers'].index

        for p, q in self.network.components['pipes'].iterrows():

            if (q['from_node'].split('-')[0] == "consumers") and (
                    q['to_node'].split('-')[0] == "consumers"):

                raise ValueError(
                    ""
                    "Pipe id {} goes from consumer to consumer. This is not "
                    "allowed!".format(p))

            if (q['from_node'].split('-')[0] == "producers") and (
                    q['to_node'].split('-')[0] == "producers"):

                raise ValueError(
                    ""
                    "Pipe id {} goes from producers to producers. "
                    "This is not allowed!".format(p))

            if ((q['from_node'].split('-')[0] == "producers") and (
                    q['to_node'].split('-')[0] == "consumers")) or ((
                        q['from_node'].split('-')[0] == "consumers") and (
                            q['to_node'].split('-')[0] == "producers")):

                raise ValueError(
                    ""
                    "Pipe id {} goes from producers directly "
                    "to consumers, or vice versa. This is not allowed!"
                    "".format(p))

            if (q['from_node'].split('-')[0] == "forks") and (
                    q['to_node'].split('-')[0] == "consumers"):

                cons_id = q['to_node'].split('-')[1]

                if cons_id not in ids_consumers:
                    raise ValueError(
                        ""
                        "The consumer of pipe id {} does not exist!".format(p))

        pipe_to_cons_ids = list(self.network.components['pipes']['to_node'].values)
        pipe_to_cons_ids = [x.split('-')[1] for x in pipe_to_cons_ids
                            if x.split('-')[0] == 'consumers']

        for id in list(self.network.components['consumers'].index):
            if id not in pipe_to_cons_ids:
                raise ValueError(
                    "The consumer id {} has no connection the the grid!".format(id))

    def remove_inactive(self):
        """
        If the attribute active is present in any of the components
        columns, or in any the investment options tables,
        all rows with active == 0 are deleted, and the column active
        is deleted.
        """
        def clean_df(df):
            if 'active' in df.columns:
                v_new = df[df['active'] == 1].copy()
                v_new.drop('active', axis=1, inplace=True)
                df = v_new
            return df

        for k, v in self.network.components.items():
            self.network.components[k] = clean_df(v)

        pipes = self.invest_options['network']['pipes']
        self.invest_options['network']['pipes'] = clean_df(pipes)

        for node_typ in ['consumers', 'producers']:
            for k, v in self.invest_options[node_typ].items():
                self.invest_options[node_typ][k] = clean_df(v)

    def complete_exist_data(self):
        """
        For all existing pipes, this method completes the attribute *invest_status* of the results
        dataframe of the pipes. If there is an existing pipe, the *invest_status* is set to 1.
        """

        pipe_types = self.invest_options['network']['pipes']
        edges = self.network.components['pipes']

        for r, c in edges.iterrows():
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

        self.network.components['pipes'] = edges

    def get_pipe_data(self):
        """Adds heat loss and investment costs to pipes dataframe.

        This method is applied for existing pipes before setting up the oemof energy system,
        and after the optimisation as part of the processing of the results.

        The columns (total) heat loss *heat_loss[kW]* and the (total) investment costs
        *invest_costs[€]* of each pipe element are calculated based on the oemof-solph results
        of the *capacity* of each pipe, the *length*, and the pipe parameters, which are looked up
        based on *label_3* from the */network/pipes.csv* of the investment options data.
        """

        pipe_types = self.invest_options['network']['pipes'].copy()
        edges = self.network.components['pipes']

        # just take active heatpipes
        edges_active = edges

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

        self.network.components['pipes'] = edges

    def setup_oemof_es(self):
        """The oemof solph energy system is initialised based on the settings,
         and filled with oemof-solph object:

         The oemof-solph objects of the *consumers* and *producers* are defined at the consumers
         and producers investment options.

         For the heating infrastructure, there is a *oemof.solph.Bus* added for every fork,
         and a pipe component for every pipe as defined in */network/pipes.csv*.
         """

        date_time_index = pd.date_range(self.settings['start_date'],
                                        periods=self.settings['num_ts'],
                                        freq=self.settings['frequence'])

        # logger.define_logging()
        logging.info('Initialize the energy system')

        self.es = solph.EnergySystem(timeindex=date_time_index)

        logging.info('Create oemof objects')

        # add houses and generation
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
        """
        Calls *check_input()*, *complete_exist_data()*, *get_pipe_data()*, and *setup_oemof_es()*,
        and does some further checks and completing the attributes of the input pipes data.
        """

        # removes all rows with attribute active == 0 - if 'active given
        self.remove_inactive()

        # initial check of pipes connections
        self.check_input()

        # create pipes attribute hp_type, if not in the table so far
        if 'hp_type' not in list(self.network.components['pipes'].columns):
            self.network.components['pipes']['hp_type'] = None

        # prepare heat data, whether global simultanity or timeseries
        if 'P_heat_max' not in list(
                self.network.components['consumers'].columns):

            df_max = self.network.sequences['consumers']['heat_flow'].max().\
                to_frame(name='P_heat_max')

            self.network.components['consumers'] = \
                pd.concat([self.network.components['consumers'], df_max],
                          axis=1, join='outer', sort=False)

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
            self.network.sequences['consumers']['heat_flow'] = df_ts

        if self.settings['num_ts'] > \
                len(self.network.sequences['consumers']['heat_flow'].index):

            raise ValueError(
                'The length of the heat demand timeseries is not sufficient '
                'for the given number of {} timesteps.'.format(
                    self.settings['num_ts']))

        # check whether there the 'existing' attribute is present at the pipes
        if 'existing' not in self.network.components['pipes'].columns:
            self.network.components['pipes']['existing'] = 0

        # get invest_status in order that .get_pipe_data() works proberly for
        # existing pipes - maybe, needs to be adapted in future
        self.complete_exist_data()

        # apply global simultaneity for demand series
        self.network.sequences['consumers']['heat_flow'] = \
            self.network.sequences['consumers']['heat_flow'] * \
            self.settings['simultaneity']

        # if there is the existing attribute, get the information about
        # the pipe types (like heat_loss)
        self.get_pipe_data()

        # set up oemof energy system
        self.setup_oemof_es()

    def solve(self):
        """Builds the oemof.solph.Model of the energysystem *es*.
        """

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
        """Postprocessing of the investment results of the pipes."""

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
            """The pipe specific investment results of the heatpipelines are
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

            ed = self.network.components['pipes']

            df_double_invest = \
                ed[(ed[hp_lab + '.' + 'size-1'] > 0.001) & (ed[hp_lab + '.' + 'size-2'] > 0.001)]

            if self.settings['print_logging_info']:
                print('***')
                if df_double_invest.empty:
                    print('There is NO investment in both directions at the'
                          'following pipes for "', hp_lab, '"')
                else:
                    print('There is an investment in both directions at the'
                          'following pipes for "', hp_lab, '":')
                    print('----------')
                    print(' id | from_node | to_node | size-1 | size-2 ')
                    print('============================================')
                    for r, c in df_double_invest.iterrows():
                        print(r, ' | ', c['from_node'], ' | ', c['to_node'],
                              ' | ', c[hp_lab + '.' + 'size-1'], ' | ',
                              c[hp_lab + '.' + 'size-2'], ' | ')
                    print('----------')

        # use pipes dataframe as base and add results as new columns to it
        df = self.network.components['pipes']

        # putting the results of the investments in heatpipes to the pipes:
        df_hp = self.invest_options['network']['pipes']

        # list of active heat pipes
        active_hp = list(df_hp['label_3'].values)

        for hp in active_hp:
            hp_param = df_hp[df_hp['label_3'] == hp].squeeze()
            get_hp_results(hp_param)
            check_multi_dir_invest(hp)

        def write_results_to_edges(pipe_data):

            def check_invest_label(hp_type, edge_id):
                if isinstance(hp_type, str):
                    raise ValueError(
                        "Pipe id {} already has an investment > 0!".format(edge_id))

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
    """
    Function for setting up the oemof solph operational Model.

    Parameters
    ----------
    thermal_network : ThermalNetwork
        See the ThermalNetwork class.
    settings : dict
        Dictionary holding the optimisation settings.
    invest_options : dict
        Dictionary holding the investment options for the district heating system.

    Returns
    -------
    model : oemof.solph.Model
        The oemof.solph.Model is build.

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
        'solve_kw': {'tee': True},
        'simultaneity': 1,
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
        edges_results = None

    results = {'oemof': model.es.results['main'],
               'oemof_meta': model.es.results['meta'],
               'components': {'pipes': edges_results}}

    return results

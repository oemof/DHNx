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
    def __init__(self, thermal_network, settings):
        self.settings = settings
        super().__init__(thermal_network)
        self.results = {}

    def setup(self):

        self.nodes = []  # list of all nodes
        self.buses = {}

        date_time_index = pd.date_range(self.settings['start_date'],
                                        periods=self.settings['time_res'],
                                        freq=self.settings['frequence'])

        # logger.define_logging()
        logging.info('Initialize the energy system')

        self.es = solph.EnergySystem(timeindex=date_time_index)

        logging.info('Create oemof objects')

        # qgis_data : ursprünglich dict mit point and line layer
        # gd_infra : invest optionen heat pipe
        # data_houses : dict mit excel/csv (buses, transformer, ...) daten von consumer
        # data_generation : dict mit excel/csv (buses, transformer, ...) daten von generation/producer

        # add heating infrastructure
        self.nodes, self.buses = add_nodes_dhs(self, self.settings, self.nodes, self.buses)
        logging.info('DHS Nodes appended.')

        # # add houses
        for typ in ['consumers', 'producers']:
            self.nodes, self.buses = add_nodes_houses(
                self, self.settings, self.nodes, self.buses, typ)

        logging.info('Producers, Consumers Nodes appended.')

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
                      **self.settings['solve_kw'])

        self.es.results['main'] = outputlib.processing.results(self.om)
        self.es.results['meta'] = outputlib.processing.meta_results(self.om)

        return

    def get_results(self):
        return self.results


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


def optimize_investment(thermal_network, settings):
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
    model = OemofInvestOptimizationModel(thermal_network, settings)

    model.solve(solver=settings['solver'], solve_kw=settings['solve_kw'])

    results = model.es.results['main']

    return results

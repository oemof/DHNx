# -*- coding: utf-8

"""
This module is designed to hold implementations of simulation models. The
implementation uses oemof/tespy.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

from tespy.components import pipe, heat_exchanger_simple
from tespy.connections import bus
from tespy.networks import network

from dhnx.tespy_facades import (
    HeatProducer,
    HeatConsumer,
    DistrictHeatingPipe,
)

from .model import SimulationModel


class SimulationModelTespy(SimulationModel):
    r"""
    Implementation of a simulation model using tespy.
    """
    def __init__(self, thermal_network):
        super().__init__(thermal_network)
        self.results = {}

    def _setup_tespy_network(self):
        r"""
        Initializes a tespy network
        """
        self.tespy_network = network(
            fluids=['water'], T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s'
        )

    def _build_tespy_componenents(self):
        temp_inlet = 90
        p_inlet = 15
        pump_efficiency = 0.8
        pr_producer = 0.99

        # # consumer
        heat_demand = 50000
        temp_return_heat_exchanger = 60
        pr_heat_exchanger = 0.99
        pr_valve = 1

        # # piping
        temp_env = 0

        # producer
        heat_producer = HeatProducer(
            'heat_producer',
            temp_inlet=temp_inlet,
            p_inlet=p_inlet,
            eta_s=pump_efficiency
        )

        # consumer
        consumer_0 = HeatConsumer(
            'consumer_0',
            Q=-heat_demand,
            temp_return_heat_exchanger=temp_return_heat_exchanger,
            pr_heat_exchanger=pr_heat_exchanger,
            pr_valve=pr_valve
        )

        # piping
        pipe_0 = DistrictHeatingPipe(
            'pipe_0',
            heat_producer,
            consumer_0,
            length=50,
            diameter=0.15,
            ks=7e-5,
            kA=10,
            temp_env=temp_env
        )

        tespy_components = [heat_producer, consumer_0, pipe_0]

        return tespy_components

    def _build_heat_accounting(self):
        # collect lost and consumed heat
        heat_losses = bus('network losses')
        heat_consumer = bus('network consumer')

        for comp in self.tespy_network.comps.index:
            if isinstance(comp, pipe):
                heat_losses.add_comps({'c': comp})

            if (isinstance(comp, heat_exchanger_simple) and '_consumer' in comp.label):
                heat_consumer.add_comps({'c': comp})

                self.tespy_network.add_busses(heat_losses, heat_consumer)

    def setup(self):
        self._setup_tespy_network()

        self.tespy_components = self._build_tespy_componenents()

        self.tespy_network.add_subsys(*self.tespy_components)

        self.tespy_network.check_network()

        self._build_heat_accounting()

        # silence warnings
        for comp in self.tespy_network.comps.index:
            comp.char_warnings = False

    def solve(self):
        self.tespy_network.solve('design')

    def get_results(self):
        self.tespy_network.print_results()
        return self.results


def simulate(thermal_network):
    r"""
    Takes a thermal network and returns the result of
    the simulation.

    Parameters
    ----------
    thermal_network

    Returns
    -------
    results : dict
    """
    model = SimulationModelTespy(thermal_network)

    model.solve()

    results = model.get_results()

    return results

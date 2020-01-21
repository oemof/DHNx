import logging

from tespy.components import (
    subsystem as Subsystem,
    cycle_closer,
    pump,
    heat_exchanger_simple,
    valve,
    pipe,
)
from tespy.connections import connection


class Facade(Subsystem):
    def __init__(self, label):
        if not isinstance(label, str):
            msg = 'Subsystem label must be of type str!'
            logging.error(msg)
            raise ValueError(msg)

        elif len([x for x in [';', ', ', '.'] if x in label]) > 0:
            msg = 'Can\'t use ' + str([';', ', ', '.']) + ' in label.'
            logging.error(msg)
            raise ValueError(msg)

        else:
            self.label = label

        self.input = None
        self.output = None
        self.comps = {}
        self.conns = {}
        self.create_comps()
        self.create_conns()


class HeatProducer(Facade):
    r"""
    A subsystem for a heat producer, comprising a source and a sink.
    """
    def __init__(self, label, temp_inlet, p_inlet, eta_s, pr=0.99):
        if not isinstance(label, str):
            msg = 'Subsystem label must be of type str!'
            logging.error(msg)
            raise ValueError(msg)

        elif len([x for x in [';', ', ', '.'] if x in label]) > 0:
            msg = 'Can\'t use ' + str([';', ', ', '.']) + ' in label.'
            logging.error(msg)
            raise ValueError(msg)

        else:
            self.label = label

        self.comps = {}
        self.conns = {}
        self.create_comps(pr, eta_s)
        self.create_conns(temp_inlet, p_inlet)

    def create_comps(self, pr, eta_s):
        self.comps['cycle_closer'] = cycle_closer(self.label + '_cycle_closer')
        self.comps['heat_exchanger'] = heat_exchanger_simple(self.label + '_heat_exchanger', pr=pr)
        self.comps['pump'] = pump(self.label + '_pump', eta_s=eta_s)
        self.output = self.comps['cycle_closer']
        self.input = self.comps['heat_exchanger']

    def create_conns(self, temp_inlet, p_inlet):
        self.conns['heat_exchanger_pump'] = connection(
            self.comps['heat_exchanger'], 'out1', self.comps['pump'], 'in1',
            T=temp_inlet, fluid={'water': 1}
        )
        self.conns['pump_cycle_closer'] = connection(
            self.comps['pump'], 'out1', self.comps['cycle_closer'], 'in1',
            p=p_inlet
        )


class HeatConsumer(Facade):
    r"""
    A subsystem for a heat consumer, comprising a heat exchanger and a valve.
    """
    def __init__(self, label, Q, temp_return_heat_exchanger, pr_valve, pr_heat_exchanger):
        if not isinstance(label, str):
            msg = 'Subsystem label must be of type str!'
            logging.error(msg)
            raise ValueError(msg)

        elif len([x for x in [';', ', ', '.'] if x in label]) > 0:
            msg = 'Can\'t use ' + str([';', ', ', '.']) + ' in label.'
            logging.error(msg)
            raise ValueError(msg)

        else:
            self.label = label

        self.comps = {}
        self.conns = {}
        self.create_comps(Q, pr_valve, pr_heat_exchanger)
        self.create_conns(temp_return_heat_exchanger)

    def create_comps(self, Q, pr_valve, pr_heat_exchanger):
        self.comps['heat_exchanger'] = heat_exchanger_simple(
            self.label + '_consumer', Q=Q, pr=pr_heat_exchanger
        )
        self.comps['valve'] = valve(self.label + '_valve', pr=pr_valve)
        self.output = self.comps['valve']
        self.input = self.comps['heat_exchanger']

    def create_conns(self, temp_return_heat_exchanger):
        self.conns['heat_exchanger_valve'] = connection(
            self.comps['heat_exchanger'], 'out1', self.comps['valve'], 'in1',
            T=temp_return_heat_exchanger,
        )


class Fork(Facade):
    r"""
    A subsystem for a fork, comprising a split and a merge.

    TODO: Allow for 2...n forks. Pass pressure losses.
    """
    def __init__(self, label):
        self.comps = {}
        self.conns = {}
        self.create_comps()
        self.create_conns()

    def create_comps(self):
        self.comps['split'] = None
        self.comps['merge'] = None

    def create_conns(self):
        self.conns['heat_exchanger_valve'] = None


class DistrictHeatingPipe(Facade):
    r"""
    A subsystem for a district heating pipe, comprising a feed and return pipe.
    """
    def __init__(self, label, start, end, length, diameter, ks, kA, temp_env):
        if not isinstance(label, str):
            msg = 'Subsystem label must be of type str!'
            logging.error(msg)
            raise ValueError(msg)

        elif len([x for x in [';', ', ', '.'] if x in label]) > 0:
            msg = 'Can\'t use ' + str([';', ', ', '.']) + ' in label.'
            logging.error(msg)
            raise ValueError(msg)

        else:
            self.label = label

        self.comps = {}
        self.conns = {}
        self.create_comps(temp_env, length, diameter, ks, kA)
        self.create_conns(start, end)

    def create_comps(self, temp_env, length, diameter, ks, kA):
        self.comps['feed'] = pipe(
            self.label + '_inlet', ks=ks, L=length, D=diameter, kA=kA, Tamb=temp_env
        )
        self.comps['return'] = pipe(
            self.label + '_return', ks=ks, L=length, D=diameter, kA=kA, Tamb=temp_env
        )

    def create_conns(self, start, end):
        self.conns['inlet_in'] = connection(start.output, 'out1', self.comps['feed'], 'in1')
        self.conns['inlet_out'] = connection(self.comps['feed'], 'out1', end.input, 'in1')
        self.conns['return_in'] = connection(end.output, 'out1', self.comps['return'], 'in1')
        self.conns['return_out'] = connection(self.comps['return'], 'out1', start.input, 'in1')

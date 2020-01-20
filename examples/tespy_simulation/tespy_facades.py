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
    def create_comps(self):
        self.comps['cycle_closer'] = cycle_closer(self.label + '_cycle_closer')
        self.comps['heat_exchanger'] = heat_exchanger_simple(self.label + '_heat_exchanger')
        self.comps['pump'] = pump(self.label + '_pump')
        self.output = self.comps['pump']
        self.input = self.comps['cycle_closer']

    def create_conns(self):
        self.conns['cycle_closer_heat_exchanger'] = connection(
            self.comps['cycle_closer'], 'out1', self.comps['heat_exchanger'], 'in1')
        self.conns['heat_exchanger_pump'] = connection(
            self.comps['heat_exchanger'], 'out1', self.comps['pump'], 'in1', T=90, p=15, fluid={'water': 1})


class HeatConsumer(Facade):
    r"""
    A subsystem for a heat consumer, comprising a heat exchanger and a valve.

    TODO: Pass Q, T_return and pressure loss
    """
    def create_comps(self):
        self.comps['heat_exchanger'] = heat_exchanger_simple(self.label + '_consumer')
        self.comps['valve'] = valve(self.label + '_valve')
        self.output = self.comps['valve']
        self.input = self.comps['heat_exchanger']

    def create_conns(self):
        self.conns['heat_exchanger_valve'] = connection(
            self.comps['heat_exchanger'], 'out1', self.comps['valve'], 'in1', T=60,
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
    def __init__(self, label, nw, start, end):
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
        self.create_comps()
        self.create_conns(nw, start, end)

    def create_comps(self):
        self.comps['feed'] = pipe(self.label + '_inlet', ks=7e-5, L=50, D=0.15, kA=10)
        self.comps['return'] = pipe(self.label + '_return', ks=7e-5, L=50, D=0.15, kA=10)

    def create_conns(self, nw, start, end):
        self.conns['inlet_in'] = connection(start.output, 'out1', self.comps['feed'], 'in1')
        self.conns['inlet_out'] = connection(self.comps['feed'], 'out1', end.input, 'in1')
        self.conns['return_in'] = connection(end.output, 'out1', self.comps['return'], 'in1')
        self.conns['return_out'] = connection(self.comps['return'], 'out1', start.input, 'in1')

from tespy.networks import network
from tespy.components import (
    subsystem as Subsystem,
    heat_exchanger_simple,
    valve,
)
from tespy.connections import connection
from tespy.connections import bus


# # TODO: connections have to be created in the background and autom. added to network
# # TODO: Check: Is this necessarily a separate step?


class HeatProducer(Subsystem):
    r"""
    A subsystem for a heat producer, comprising a source and a sink.
    """
    def create_comps(self):
        self.comps['source'] = None
        self.comps['sink'] = None

    def create_conns(self):
        self.conns['conn'] = None


class HeatConsumer(Subsystem):
    r"""
    A subsystem for a heat consumer, comprising a heat exchanger and a valve.
    """
    def create_comps(self):
        self.comps['heat_exchanger'] = heat_exchanger_simple(self.label + '_consumer')
        self.comps['valve'] = valve(self.label + '_valve')

    def create_conns(self):
        self.conns['heat_exchanger_valve'] = connection(
            self.comps['heat_exchanger'], 'out1', self.comps['valve'], 'in1', T=60,
        )


class Fork(Subsystem):
    r"""
    A subsystem for a fork, comprising a split and a merge.
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


class DistrictHeatingPipe(Subsystem):
    r"""
    A subsystem for a district heating pipe, comprising a feed and return pipe.
    """
    def __init__(self, label, start, end):
        self.comps = {}
        self.conns = {}
        self.create_comps()
        self.create_conns()

    def create_comps(self):
        self.comps['feed'] = None
        self.comps['return'] = None

    def create_conns(self):
        self.conns['conn'] = None

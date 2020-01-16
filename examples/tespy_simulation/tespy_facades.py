from tespy.networks import network
from tespy.connections import bus


class Facade():
    def __init__(self):
        pass


class HeatProducer(Facade):
    def __init__(self):
        pass


class HeatConsumer(Facade):
    def __init__(self):
        pass


class Split(Facade):
    def __init__(self):
        pass


class DistrictHeatingPipe(Facade):
    def __init__(self, source, target):
        pass


nw = network(fluids=['water'], T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s')

pipe1 = DistrictHeatingPipe
# TODO: connections have to be created in the background and autom. added to network

# TODO: Check: Is this necessarily a separate step?
heat_losses = bus('network losses')
heat_consumer = bus('network consumer')

nw.check_network()
nw.solve('design')

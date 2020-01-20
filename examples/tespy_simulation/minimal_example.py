from tespy.components import pipe, heat_exchanger_simple
from tespy.connections import bus
from tespy.networks import network

from tespy_facades import (
    HeatProducer,
    HeatConsumer,
    DistrictHeatingPipe,
)


# This is a minimal example of a district heating network
# TODO: Check if solution is correct
# TODO: Setup a builder
# TODO: Solve a tree-like network
# TODO: Try solving a network with loops

nw = network(
    fluids=['water'], T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s'
)

# producer
heat_producer = HeatProducer('heat_producer')
heat_producer.comps['heat_exchanger'].set_attr(pr=0.99)
heat_producer.comps['pump'].set_attr(eta_s=0.8)

# consumer
consumer_0 = HeatConsumer('consumer_0')
consumer_0.comps['heat_exchanger'].set_attr(Q=-5e4, pr=0.99)
consumer_0.comps['valve'].set_attr(pr=1)

# piping
pipe_0 = DistrictHeatingPipe('pipe_0', heat_producer, consumer_0)

nw.add_subsys(heat_producer, consumer_0, pipe_0)

# collect lost and consumed heat
heat_losses = bus('network losses')
heat_consumer = bus('network consumer')

nw.check_network()

for comp in nw.comps.index:
    if isinstance(comp, pipe):

        comp.set_attr(Tamb=0)

        heat_losses.add_comps({'c': comp})

    if (isinstance(comp, heat_exchanger_simple) and not isinstance(comp, pipe)):
        heat_consumer.add_comps({'c': comp})

nw.add_busses(heat_losses, heat_consumer)

# silence warnings
for comp in nw.comps.index:
    comp.char_warnings = False

# solve
nw.solve('design')
nw.save('minimal_example')

print('Heat demand consumer:', heat_consumer.P.val)
print('network losses at 0 °C outside temperature (design):', heat_losses.P.val)

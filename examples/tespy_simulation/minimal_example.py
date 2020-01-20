from tespy.components import pipe, heat_exchanger_simple
from tespy.connections import bus
from tespy.networks import network

from tespy_facades import (
    HeatProducer,
    HeatConsumer,
    DistrictHeatingPipe,
)

# assumptions
# # producer
temp_inlet = 90
p_inlet = 15
pump_efficiency = 0.8
pr_producer = 0.99

# # consumer
heat_demand = 5e4
pr_heat_exchanger = 0.99
pr_valve = 1

# # piping
temp_env = 0


# This is a minimal example of a district heating network
# TODO: Check if solution is correct
# TODO: Setup a builder
# TODO: Solve a tree-like network
# TODO: Try solving a network with loops

nw = network(
    fluids=['water'], T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s'
)

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
    pr_heat_exchanger=pr_heat_exchanger,
    pr_valve=pr_valve
)

# piping
pipe_0 = DistrictHeatingPipe(
    'pipe_0',
    heat_producer,
    consumer_0,
    temp_env=temp_env
)

nw.add_subsys(heat_producer, consumer_0, pipe_0)

# collect lost and consumed heat
heat_losses = bus('network losses')
heat_consumer = bus('network consumer')

nw.check_network()

for comp in nw.comps.index:
    if isinstance(comp, pipe):
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

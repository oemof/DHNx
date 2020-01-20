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
heat_demand = 50000
temp_return_heat_exchanger = 60
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
    temp_return_heat_exchanger=temp_return_heat_exchanger,
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

    if (isinstance(comp, heat_exchanger_simple) and '_consumer' in comp.label):
        heat_consumer.add_comps({'c': comp})

nw.add_busses(heat_losses, heat_consumer)

# silence warnings
for comp in nw.comps.index:
    comp.char_warnings = False

# solve
nw.solve('design')
nw.save('minimal_example')

overview_results = {
    'Heat demand consumer': heat_consumer.P.val,
    'Heat feedin producer': heat_producer.comps['heat_exchanger'].Q.val,
    f'Network losses': heat_losses.P.val,
    f'Relative network losses': round(
        heat_losses.P.val / heat_producer.comps['heat_exchanger'].Q.val, 4
    ),
    'Mass flow at producer': heat_producer.conns['heat_exchanger_pump'].m.val,
    'Temperature diff. at producer': round(
        heat_producer.conns['heat_exchanger_pump'].T.val
        - pipe_0.conns['return_out'].T.val, 2
    ),
    'Pressure pump_pipe': heat_producer.conns['pump_cycle_closer'].p.val,
    'Pressure heat_exchanger_pump': heat_producer.conns['heat_exchanger_pump'].p.val,
    'Pressure ratio': heat_producer.comps['pump'].pr.val,
    'Pump power': heat_producer.comps['pump'].P.val,
}

dash = '-' * 50

print(dash)
print('{:>32s}{:>15s}'.format('Parameter name', 'Value'))
print(dash)

for key, value in overview_results.items():
    print('{:>32s}{:>15.5f}'.format(key, value))

from tespy.components import source, sink, pipe, heat_exchanger_simple
from tespy.connections import connection, bus
from tespy.networks import network

from tespy_facades import HeatConsumer


# This is a test of a minimal example of a district heating network
# TODO: Check if solution is correct
# TODO: Create the same network using functions
# TODO: Try solving a network with loops
# TODO: Setup tespy-facades and a builder

nw = network(
    fluids=['water'], T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s'
)

# producer
# hint might be replaced by: cyclecloser
so = source('heat source feed-in')
si = sink('heat source return')

# consumer (housing area 4)
consumer_0 = HeatConsumer('consumer_0')
consumer_0.comps['heat_exchanger'].set_attr(Q=-5e4, pr=0.99)
consumer_0.comps['valve'].set_attr(pr=1)

nw.add_subsys(consumer_0)

# piping
pipe_0_i = pipe('pipe0_inlet', ks=7e-5, L=50, D=0.15, kA=10)
pipe_0_r = pipe('pipe0_return', ks=7e-5, L=50, D=0.15, kA=10)

con_0 = connection(so, 'out1', pipe_0_i, 'in1', T=90, p=15, fluid={'water': 1})
con_1 = connection(pipe_0_i, 'out1', consumer_0.comps['heat_exchanger'], 'in1')

con_2 = connection(consumer_0.comps['valve'], 'out1', pipe_0_r, 'in1')
con_3 = connection(pipe_0_r, 'out1', si, 'in1')

cons = [
    con_0,
    con_1,
    con_2,
    con_3,
]

heat_losses = bus('network losses')
heat_consumer = bus('network consumer')

nw.add_conns(*cons)
nw.check_network()

# set attributes
for comp in nw.comps.index:
    if isinstance(comp, pipe):

        comp.set_attr(Tamb=0)

        heat_losses.add_comps({'c': comp})

    if (isinstance(comp, heat_exchanger_simple) and not isinstance(comp, pipe)):
        heat_consumer.add_comps({'c': comp})

nw.add_busses(heat_losses, heat_consumer)

for comp in nw.comps.index:
    comp.char_warnings = False

nw.solve('design')
nw.save('minimal_example')

print('Heat demand consumer:', heat_consumer.P.val)
print('network losses at 0 °C outside temperature (design):', heat_losses.P.val)

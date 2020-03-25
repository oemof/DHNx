from tespy.components import source, sink, pipe, heat_exchanger_simple
from tespy.connections import connection, bus
from tespy.networks import network

from sub_consumer import lin_consum_closed, fork as fo


# This is a test of a minimal example of a district heating network
# TODO: Provide the right amount of variables and solve the network
# TODO: Check if solution is correct
# TODO: Create the same network using functions
# TODO: Try solving a network with loops
# TODO: Setup tespy-facades and a builder

nw = network(
    fluids=['water'], T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s'
)

# producer
# hint might be replaced by: cyclecloser
so = source('source')
si = sink('sink')

# split
fo_0 = fo('split_0', 2)

# consumer (housing area 4)
consumer_0 = lin_consum_closed('consumer_0', 2)
consumer_0.comps['consumer_0'].set_attr(Q=-5e4, pr=0.99)
consumer_0.comps['consumer_1'].set_attr(Q=-5e4, pr=0.99)
consumer_0.comps['feed_0'].set_attr(ks=7e-5, L=150, D=0.15, offdesign=['kA'])
consumer_0.comps['return_0'].set_attr(ks=7e-5, L=150, D=0.15, offdesign=['kA'])

consumer_1 = lin_consum_closed('consumer_1', 2)
consumer_1.comps['consumer_0'].set_attr(Q=-5e4, pr=0.99)
consumer_1.comps['consumer_1'].set_attr(Q=-5e4, pr=0.99)
consumer_1.comps['feed_0'].set_attr(ks=7e-5, L=150, D=0.15, offdesign=['kA'])
consumer_1.comps['return_0'].set_attr(ks=7e-5, L=150, D=0.15, offdesign=['kA'])

nw.add_subsys(consumer_0, consumer_1)

# pipings

# first
pipe_0_i = pipe('pipe0_inlet', ks=7e-5, L=50, D=0.15, offdesign=['kA'])
pipe_0_r = pipe('pipe0_return', ks=7e-5, L=50, D=0.15, offdesign=['kA'])

con_0 = connection(so, 'out1', pipe_0_i, 'in1', T=90, p=15, fluid={'water': 1})
con_1 = connection(pipe_0_i, 'out1', fo_0.comps['splitter'], 'in1')

con_2 = connection(fo_0.comps['merge'], 'out1', pipe_0_r, 'in1')
con_3 = connection(pipe_0_r, 'out1', si, 'in1')


# second
pipe_1_i = pipe('pipe1_inlet', ks=7e-5, L=50, D=0.15, offdesign=['kA'])
pipe_1_r = pipe('pipe1_return', ks=7e-5, L=50, D=0.15, offdesign=['kA'])

con_4 = connection(fo_0.comps['splitter'], 'out1', pipe_1_i, 'in1')
con_5 = connection(pipe_1_i, 'out1', consumer_0.comps['splitter_0'], 'in1')

con_6 = connection(consumer_0.comps['merge_0'], 'out1', pipe_1_r, 'in1')
con_7 = connection(pipe_1_r, 'out1', fo_0.comps['merge'], 'in1')


# third
pipe_2_i = pipe('pipe2_inlet', ks=7e-5, L=50, D=0.15, offdesign=['kA'])
pipe_2_r = pipe('pipe2_return', ks=7e-5, L=50, D=0.15, offdesign=['kA'])

con_8 = connection(fo_0.comps['splitter'], 'out2', pipe_2_i, 'in1')
con_9 = connection(pipe_2_i, 'out1', consumer_1.comps['splitter_0'], 'in1')

con_10 = connection(consumer_1.comps['merge_0'], 'out1', pipe_2_r, 'in1')
con_11 = connection(pipe_2_r, 'out1', fo_0.comps['merge'], 'in2')


cons = [
    con_0,
    con_1,
    con_2,
    con_3,
    con_4,
    con_5,
    con_6,
    con_7,
    con_8,
    con_9,
    con_10,
    con_11,
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

nw.print_results()

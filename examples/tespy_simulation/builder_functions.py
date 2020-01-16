from tespy.components import (
    source,
    sink,
    pipe,
)
from tespy.connections import connection, bus

from sub_consumer import lin_consum_closed, fork


def add_producer():
    so = source('source')
    si = sink('sink')
    new_producer = [so, si]
    return new_producer


def add_consumer(network, label):
    new_consumer = lin_consum_closed(label, 2)
    new_consumer.comps['consumer_0'].set_attr(Q=-5e4, pr=0.99)
    new_consumer.comps['consumer_1'].set_attr(Q=-5e4, pr=0.99)
    new_consumer.comps['feed_0'].set_attr(ks=7e-5, L=150, D=0.15, offdesign=['kA'])
    network.add_subsys(new_consumer)

    return new_consumer


def add_split(network, label, number):
    new_split = fork(label, number)

    return new_split


def add_pipe(network, label, source, target):
    new_pipe = pipe(label, ks=7e-5, L=50, D=0.15, offdesign=['kA'])

    con_source_inlet = connection(source, 'out1', new_pipe, 'in1', T=90, p=15, fluid={'water': 1})
    con_inlet_target = connection(new_pipe, 'out1', target, 'in1', T=90, p=15, fluid={'water': 1})

    con_target_return = connection(target, 'out1', new_pipe, 'in1', T=90, p=15, fluid={'water': 1})
    con_return_source = connection(new_pipe, 'out1', target, 'in1', T=90, p=15, fluid={'water': 1})
    network.add(con_source_inlet, con_inlet_target, con_target_return, con_return_source)

    return network


heat_losses = bus('network losses')
heat_consumer = bus('network consumer')

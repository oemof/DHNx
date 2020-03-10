from collections import OrderedDict
import itertools as it
import os.path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import xarray as xr

from tespy.components import pipe, heat_exchanger_simple
from tespy.connections import bus
from tespy.networks import network
from dhnx.tespy_facades import (
    HeatProducer,
    HeatConsumer,
    DistrictHeatingPipe,
)

lamb_func = (
    lambda eps, D, Re: 1.325 / (np.log(eps / (3.7 * D) + 5.74 / (Re ** 0.9))) ** 2
)


def single_pipe(args):
    r"""
    Calculate hydraulic and thermal properties of a single feed and return
    district heating pipe.
    """
    Q_cons, DT_drop, DT_prod_in, k, L, D, c, rho, eps, mu = args
    Q_cons *= 1e6  # MW to W
    eta_pump = 0.7
    pressure_loss_cons = 1

    nw = network(
        fluids=['water'], T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s'
    )

    # producer
    heat_producer = HeatProducer(
        'heat_producer',
        temp_inlet=DT_prod_in,
        p_inlet=15,  # TODO check
        eta_s=eta_pump
    )

    # consumer
    consumer_0 = HeatConsumer(
        'consumer_0',
        Q=-Q_cons,
        temp_return_heat_exchanger=DT_prod_in - 10,
        pr_heat_exchanger=(15-pressure_loss_cons)/15,
        pr_valve=1
    )

    # piping
    pipe_0 = DistrictHeatingPipe(
        'pipe_0',
        heat_producer,
        consumer_0,
        length=L,
        diameter=D,
        ks=eps,
        kA=1000,
        temp_env=0
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

    # Collect results
    Q_prod = heat_producer.comps['heat_exchanger'].Q.val
    DT_cons_in = pipe_0.conns['inlet_out'].T.val
    DT_prod_r = pipe_0.conns['return_out'].T.val
    v = heat_producer.conns['heat_exchanger_pump'].v.val / (0.25 * np.pi * D**2)
    pressure_loss_bar = (
        heat_producer.conns['pump_cycle_closer'].p.val
        - heat_producer.conns['heat_exchanger_pump'].p.val
    )
    print(pressure_loss_bar, heat_producer.conns['pump_cycle_closer'].p.unit)
    P_pump_kW = 1e-3 * heat_producer.comps['pump'].P.val
    Q_loss_MW = - 1e-6 * heat_losses.P.val
    perc_loss = - 100 * heat_losses.P.val / heat_producer.comps['heat_exchanger'].Q.val

    if DT_prod_r > 0:
        return np.array(
            [
                Q_prod,
                DT_cons_in,
                DT_prod_r,
                v,
                pressure_loss_bar,
                P_pump_kW,
                Q_loss_MW,
                perc_loss,
            ]
        )
    else:
        return None


def generic_sampling(input_dict, results_dict, function):
    r"""
    n-dimensional full sampling, storing as xarray.

    Parameters
    ----------
    input_dict : OrderedDict
        Ordered dictionary containing the ranges of the
        dimensions.

    results_dict : OrderedDict
        Ordered dictionary containing the dimensions and
        coordinates of the results of the function.

    function : function
        Function to be sampled.

    Returns
    -------
    results : xarray.DataArray

    sampling : np.array

    indices :
    """
    join_dicts = OrderedDict(list(input_dict.items()) + list(results_dict.items()))
    dims = join_dicts.keys()
    coords = join_dicts.values()
    results = xr.DataArray(
        np.empty([len(v) for v in join_dicts.values()]), dims=dims, coords=coords
    )

    sampling = np.array(list(it.product(*input_dict.values())))
    indices = np.array(
        list(it.product(*[np.arange(len(v)) for v in input_dict.values()]))
    )

    for i in range(len(sampling)):
        print(f'Calculating {i} of {len(sampling)} results')
        result = function(sampling[i])
        results[tuple(indices[i])] = result

    return results, sampling, indices


input_dict = OrderedDict(
    [
        ('Q_cons', np.arange(1, 6, 2)),
        ('DT_drop', [10]),
        ('DT_prod_in', [70, 90, 110]),
        ('k', np.arange(1, 3, 1)),
        ('L', [1000]),
        ('D', [0.25, 0.3, 0.4]),
        ('c', [4230]),
        ('rho', [951]),
        ('eps', [0.01e-3]),
        ('mu', [0.255e-3]),
    ]
)

result_dict = OrderedDict(
    [
        (
            'results',
            [
                'Q_prod',
                'DT_cons_in',
                'DT_prod_r',
                'v [m/s]',
                'pressure_loss [bar]',
                'P_pump [kW]',
                'Q_loss [MW]',
                'loss [%]',
            ],
        )
    ]
)


def plot_data():
    r"""

    """
    fig, axs = plt.subplots(5, 3, figsize=(9, 12))

    coords = ['D', 'DT_prod_in', 'k']
    ylim = [(0, 3), (0, 5), (0, 300), (0.1, 0.5), (0, 30)]
    colors = [
        sns.color_palette("hls", len(sam_results[coord])).as_hex() for coord in coords
    ]
    labels = [
        [f'{coord}={D}' for D in sam_results.coords[coord].values] for coord in coords
    ]
    titles = [
        'Flow velocity',
        'Pressure loss',
        'Pump power',
        'Heat loss',
        'Relative heat loss',
    ]

    for i, c in enumerate(
        ['v [m/s]', 'pressure_loss [bar]', 'P_pump [kW]', 'Q_loss [MW]', 'loss [%]']
    ):

        for ii, vv in enumerate(sam_results.coords['D'].values):
            sam_results.squeeze().isel(k=1, DT_prod_in=-1).sel(results=c, D=vv).plot(
                ax=axs[i, 0], marker='.', markersize=10, color=colors[0][ii]
            )

            axs[i, 0].set_ylim(ylim[i])
            axs[i, 0].set_xlabel('Q_cons [MW]')
            axs[i, 0].set_ylabel(c)
            axs[i, 0].set_title('', size='15')
        axs[0, 0].set_title('Column A \n', size='15')
        axs[-1, 0].set_xlabel('Q_cons [MW] \n\n DT_prod_in=110°C \n k=1.5 W/(m²K)')

        for ii, vv in enumerate(sam_results.coords['DT_prod_in'].values):
            sam_results.squeeze().isel(k=1, DT_prod_in=ii).sel(results=c, D=0.25).plot(
                ax=axs[i, 1], marker='.', markersize=10, color=colors[1][ii]
            )

            axs[i, 1].set_ylim(ylim[i])
            axs[i, 1].set_xlabel('Q_cons [MW]')
            axs[i, 1].set_title(titles[i], size='15')
        axs[0, 1].set_title('Column B \n' + titles[0], size='15')
        axs[-1, 1].set_xlabel('Q_cons [MW] \n\n D=0.25 \n k=1.5 W/(m²K)')

        for ii, vv in enumerate(sam_results.coords['k'].values):
            sam_results.squeeze().isel(k=ii, DT_prod_in=-1).sel(results=c, D=0.25).plot(
                ax=axs[i, 2], marker='.', markersize=10, color=colors[2][ii]
            )

            axs[i, 2].set_ylim(ylim[i])
            axs[i, 2].set_xlabel('Q_cons [MW]')
            axs[i, 2].set_title('', size='15')
        axs[0, 2].set_title('Column C \n', size='15')
        axs[-1, 2].set_xlabel('Q_cons [MW] \n\n D=0.25 m \n DT_prod_in=110°C')

    plt.subplots_adjust(hspace=0.7)

    for i, coord in enumerate(coords):
        axs[-1, i].legend(
            axs[-1, i],
            labels=labels[i],
            loc='lower center',
            bbox_to_anchor=(0.5, -1.8),
            ncol=1,
        )

    # plt.tight_layout()
    fig.savefig('tespy_single_pipe_calculations.pdf', bbox_inches="tight")


if os.path.isfile('tespy_single_pipe_calculations.nc'):
    print('File exists')
    sam_results = xr.open_dataarray('tespy_single_pipe_calculations.nc')

else:
    print('Calculate')
    sam_results = generic_sampling(input_dict, result_dict, single_pipe)[0]
    sam_results.to_netcdf('tespy_single_pipe_calculations.nc')

plot_data()

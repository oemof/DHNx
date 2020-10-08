# -*- coding: utf-8

"""
This module is designed to hold auxilary functions for dhnx optimization.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

from oemof.tools import economics


def precalc_cost_param(t, q, gd):
    """
    Parameters
    ----------
    t : series of heatpipeline data row
    q : series of pipes row
    gd : general optimisation settings

    Returns
    -------

    """

    if t['annuity']:
        epc_p = float(economics.annuity(
            capex=t['capex_pipes'] * q['length[m]'],
            n=t['n_pipes'], wacc=gd['rate']))
        epc_fix = float(economics.annuity(
            capex=t['fix_costs'] * q['length[m]'],
            n=t['n_pipes'], wacc=gd['rate']))
    else:
        epc_p = t['capex_pipes'] * q['length[m]']
        epc_fix = t['fix_costs'] * q['length[m]']

    return epc_p, epc_fix

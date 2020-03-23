# -*- coding: utf-8

"""
This module is designed to hold optimization model implementations. The
implementation makes use of oemof-solph.

This file is part of project dhnx (). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location:

SPDX-License-Identifier: MIT
"""

from pyomo.core.base.block import SimpleBlock
from pyomo.environ import (Binary, Set, NonNegativeReals, Var, Constraint,
                           Expression, BuildAction)
import logging

from oemof.solph.network import Bus, Transformer
from oemof.solph.plumbing import sequence
from oemof.solph import Investment
from collections import namedtuple


class Label(namedtuple('solph_label', ['tag1', 'tag2', 'tag3', 'tag4'])):
    __slots__ = ()

    def __str__(self):
        """The string is used within solph as an ID, so it hast to be unique"""
        return '_'.join(map(str, self._asdict().values()))


class HeatPipeline(Transformer):
    r"""A HeatPipeline represent a Pipeline in a district heating system.
    This is done by a Transformer with a constant energy loss independent of
    actual power, but dependent on the nominal power and the length parameter.
    The HeatPipeline is a single-input-single-output transformer. Additionally,
    conversion factors for in- and output flow can be applied.

    Parameters
    ----------
    length : float
        Length of HeatPipeline.
    heat_loss_factor : float
        Heat loss per length unit as fraction of the nominal power. Can also be
        defined by a series.

    See also :py:class:`~oemof.solph.network.Transformer`.

    Note
    ----
    This component is experimental. Use it with care.


    The following sets, variables, constraints and objective parts are created
     * :py:class:`~oemof.solph.custom.HeatPipelineBlock` (if no
       Investment object present)
     * :py:class:`~oemof.solph.custom.HeatPipelineInvestBlock` (if
       Investment object present)

    Examples
    --------
    example

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.length = kwargs.get('length')
        self.heat_loss_factor = sequence(kwargs.get('heat_loss_factor'))
        self.heat_loss_factor_fix = sequence(kwargs.get('heat_loss_factor_fix'))

        self._invest_group = False

        if len(self.inputs) > 1 or len(self.outputs) > 1:
            raise ValueError("Heatpipe must not have more than \
                             one input and one output!")

        for f in self.inputs.values():
            if f.nonconvex is not None:
                raise ValueError(
                    "Attribute `nonconvex` of component `HeatPipeline`" +
                    "has not been tested yet.")

        for f in self.outputs.values():
            if f.nonconvex is not None:
                raise ValueError(
                    "Attribute `nonconvex` of component `HeatPipeline`" +
                    "has not been tested yet.")

        self._check_flows()

    def _check_flows(self):
        for flow in self.inputs.values():
            if isinstance(flow.investment, Investment):
                self._invest_group = True

        for flow in self.outputs.values():
            if isinstance(flow.investment, Investment):
                self._invest_group = True

    def constraint_group(self):
        if self._invest_group is True:
            return HeatPipelineInvestBlock
        else:
            return HeatPipelineBlock


class HeatPipelineBlock(SimpleBlock):
    r"""Block representing a pipeline of a district heating system.
    :class:`~oemof.solph.custom.HeatPipeline`

    **The following constraints are created:**

    .. _HeatPipelineBlock-equations:

    .. math::
        &
        (1) \dot{Q}_{out}(t) = \dot{Q}_{in}(t) \cdot
        \frac{\eta_{out}}{\eta_{in}} - \dot{Q}_{loss}(t)\\
        &
        (2) \dot{Q}_{loss}(t) = f_{loss}(t) \cdot l \cdot \dot{Q}_{nominal}
        &

    The symbols used are defined as follows
    (with Variables (V) and Parameters (P)):

    .. csv-table::
        :header: "symbol", "attribute", "type", "explanation"
        :widths: 1, 1, 1, 1

        ":math:`\dot{Q}_{out}(t)`", ":py:obj:`flow[n, o, t]`", "V", "Heat
        output"
        ":math:`\dot{Q}_{in}(t)`", ":py:obj:`flow[i, n, t]`", "V", "Heat input"
        ":math:`\dot{Q}_{loss}(t)`", ":py:obj:`heat_loss[n, t]`", "P", "Heat
        loss of heat pipeline"
        ":math:`\dot{Q}_{nominal}`", ":py:obj:`flows[n, o].nominal_value`", "
        P", "Nominal capacity of heating pipeline"
        ":math:`\eta_{out}`", ":py:obj:`conversion_factors[o][t]`", "P", "
        Conversion factor of output flow (Heat Output)"
        ":math:`\eta_{in}`", ":py:obj:`conversion_factors[i][t]`", "P", "
        Conversion factor of input flow (Heat Input)"
        ":math:`f_{loss}(t)`", ":py:obj:`heat_loss_factor`", "P", "Specific
        heat loss factor for pipeline"
        ":math:`l`", ":py:obj:`length`", "P", "Length of heating pipeline"


    """

    CONSTRAINT_GROUP = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _create(self, group=None):
        """ Creates the linear constraint for the class:`Heatpipe`
        block.

        Parameters
        ----------
        group : list

        """
        if group is None:
            return None

        m = self.parent_block()

        self.HEATPIPES = Set(initialize=[n for n in group])

        # Defining Variables
        self.heat_loss = Var(self.HEATPIPES, m.TIMESTEPS,
                             within=NonNegativeReals)

        def _heat_loss_rule(block, n, t):
            """Rule definition for constraint to connect the installed capacity
            and the heat loss
            """
            o = list(n.outputs.keys())[0]

            expr = 0
            expr += - block.heat_loss[n, t]
            expr +=\
                n.heat_loss_factor[t] * n.length * m.flows[n, o].nominal_value
            return expr == 0

        self.heat_loss_equation = Constraint(self.HEATPIPES, m.TIMESTEPS,
                                             rule=_heat_loss_rule)

        def _relation_rule(block, n, t):
            """Link input and output flow and subtract heat loss."""
            i = list(n.inputs.keys())[0]
            o = list(n.outputs.keys())[0]

            expr = 0
            expr += - m.flow[n, o, t]
            expr += m.flow[i, n, t] * n.conversion_factors[
                o][t] / n.conversion_factors[i][t]
            expr += - block.heat_loss[n, t]
            return expr == 0

        self.relation = Constraint(self.HEATPIPES, m.TIMESTEPS,
                                   rule=_relation_rule)


class HeatPipelineInvestBlock(SimpleBlock):
    r"""Block representing a pipeline of a district heating system.
    :class:`~oemof.solph.custom.HeatPipeline`

    **The following constraints are created:**

    .. _HeatPipelineInvestBlock-equations:

    .. math::
        &
        (1) \dot{Q}_{out}(t) = \dot{Q}_{in}(t) \cdot
        \frac{\eta_{out}}{\eta_{in}} - \dot{Q}_{loss}(t)\\
        &
        (2) \dot{Q}_{loss}(t) = f_{loss}(t) \cdot l \cdot \dot{Q}_{nominal}
        &

    The symbols used are defined as follows
    (with Variables (V) and Parameters (P)):

    .. csv-table::
        :header: "symbol", "attribute", "type", "explanation"
        :widths: 1, 1, 1, 1

        ":math:`\dot{Q}_{out}(t)`", ":py:obj:`flow[n, o, t]`", "V", "Heat
        output"
        ":math:`\dot{Q}_{in}(t)`", ":py:obj:`flow[i, n, t]`", "V", "Heat input"
        ":math:`\dot{Q}_{loss}(t)`", ":py:obj:`heat_loss[n, t]`", "V", "Heat
        loss of heat pipeline"
        ":math:`\dot{Q}_{nominal}`", ":py:obj:`flows[n, o].nominal_value`", "
        V", "Nominal capacity of heating pipeline"
        ":math:`\eta_{out}`", ":py:obj:`conversion_factors[o][t]`", "P", "
        Conversion factor of output flow (heat output)"
        ":math:`\eta_{in}`", ":py:obj:`conversion_factors[i][t]`", "P", "
        Conversion factor of input flow (heat input)"
        ":math:`f_{loss}(t)`", ":py:obj:`heat_loss_factor`", "P", "Specific
        heat loss factor for pipeline"
        ":math:`l`", ":py:obj:`length`", "P", "Length of heating pipeline"


    """

    CONSTRAINT_GROUP = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _create(self, group=None):
        """ Creates the linear constraint for the class:`HeatPipeline`
        block.

        Parameters
        ----------
        group : list

        """
        if group is None:
            return None

        m = self.parent_block()

        # Defining Sets
        self.INVESTHEATPIPES = Set(initialize=[n for n in group])
        self.CONVEX_INVESTHEATPIPES = Set(initialize=[
            n for n in group if n.outputs[list(n.outputs.keys())[0]].investment.nonconvex is False])
        self.NONCONVEX_INVESTHEATPIPES = Set(initialize=[
            n for n in group if n.outputs[list(n.outputs.keys())[0]].investment.nonconvex is True])

        # Defining Variables
        self.heat_loss = Var(self.INVESTHEATPIPES, m.TIMESTEPS,
                             within=NonNegativeReals)

        def _heat_loss_rule_convex(block, n, t):
            """Rule definition for constraint to connect the installed capacity
            and the heat loss
            """
            expr = 0
            expr += - block.heat_loss[n, t]
            expr += n.heat_loss_factor[t] * n.length * m.InvestmentFlow.invest[
                n, list(n.outputs.keys())[0]]
            return expr == 0
        self.heat_loss_equation_convex = Constraint(self.CONVEX_INVESTHEATPIPES, m.TIMESTEPS,
                                             rule=_heat_loss_rule_convex)

        def _heat_loss_rule_nonconvex(block, n, t):
            """Rule definition for constraint to connect the installed capacity
            and the heat loss
            """
            expr = 0
            expr += - block.heat_loss[n, t]
            expr += n.heat_loss_factor[t] * n.length * m.InvestmentFlow.invest[
                n, list(n.outputs.keys())[0]]
            expr += n.heat_loss_factor_fix[t] * n.length * m.InvestmentFlow.invest_status[
                n, list(n.outputs.keys())[0]]
            return expr == 0
        self.heat_loss_equation_nonconvex = Constraint(self.NONCONVEX_INVESTHEATPIPES, m.TIMESTEPS,
                                             rule=_heat_loss_rule_nonconvex)

        def _relation_rule(block, n, t):
            """Link input and output flow and subtract heat loss."""
            i = list(n.inputs.keys())[0]
            o = list(n.outputs.keys())[0]

            expr = 0
            expr += - m.flow[n, o, t]
            expr += m.flow[i, n, t] * n.conversion_factors[
                o][t] / n.conversion_factors[i][t]
            expr += - block.heat_loss[n, t]
            return expr == 0

        self.relation = Constraint(self.INVESTHEATPIPES, m.TIMESTEPS,
                                   rule=_relation_rule)

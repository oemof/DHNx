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

        self.length = kwargs.get('length', 1)
        self.heat_loss_factor = sequence(kwargs.get('heat_loss_factor', 0))
        self.heat_loss_factor_fix = sequence(kwargs.get(
            'heat_loss_factor_fix', 0))

        self._invest_group = False
        self._nonconvex_group = False

        if len(self.inputs) > 1 or len(self.outputs) > 1:
            raise ValueError("Heatpipe must not have more than"
                             " one input and one output!")

        for f in self.inputs.values():
            if f.nonconvex is not None:
                raise ValueError(
                    "Inputflow must not be of type NonConvexFlow!")

        for f in self.outputs.values():
            if f.nonconvex is not None:
                self._nonconvex_group = True

        self._check_flows_invest()

        if (self._nonconvex_group is True) and (self._invest_group is True):
            raise ValueError(
                "Either an investment OR a switchable heatloss can be set"
                " (NonConvexFlow)."
                " Remove the NonConvexFlow or drop "
                "the Investment attribute.")

        if self._invest_group is True:
            o = list(self.outputs.keys())[0]
            if (self.heat_loss_factor_fix[0] > 0) \
                    and (self.outputs[o].investment.nonconvex is False):
                raise ValueError(
                    "In case of a convex Investment (Investment.nonconvex is "
                    " False), the 'heat_loss_factor_fix' is not considered!"
                    " Set the heat_loss_factor_fix to 0!")

    def _check_flows_invest(self):
        for flow in self.inputs.values():
            if isinstance(flow.investment, Investment):
                raise ValueError(
                    "The investment must be defined at the Outputflow!")

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
        self.CONVEX_HEATPIPES = Set(initialize=[n for n in group if n.outputs[list(n.outputs.keys())[0]].nonconvex is None])
        self.NONCONVEX_HEATPIPES = Set(initialize=[n for n in group if n.outputs[list(n.outputs.keys())[0]].nonconvex is not None])

        # Defining Variables
        self.heat_loss = Var(self.HEATPIPES, m.TIMESTEPS,
                             within=NonNegativeReals)

        def _heat_loss_rule_fix(block, n, t):
            """Rule definition for the heat loss depending on the nominal
            capacity for fix fix heat loss.
            """
            o = list(n.outputs.keys())[0]

            expr = 0
            expr += - block.heat_loss[n, t]
            expr +=\
                n.heat_loss_factor[t] * n.length * m.flows[n, o].nominal_value
            expr += n.heat_loss_factor_fix[t] * n.length
            return expr == 0

        self.heat_loss_equation_fix = Constraint(
            self.CONVEX_HEATPIPES, m.TIMESTEPS, rule=_heat_loss_rule_fix)

        def _heat_loss_rule_on_off(block, n, t):
            """Rule definition for the heat loss depending on the nominal
            capacity. Here, the losses can be "switched off".
            """
            o = list(n.outputs.keys())[0]

            expr = 0
            expr += - block.heat_loss[n, t]
            expr += (n.heat_loss_factor[t] * m.flows[n, o].nominal_value +
                     n.heat_loss_factor_fix[t]) * n.length * m.NonConvexFlow.status[n, o, t]
            return expr == 0

        self.heat_loss_equation_on_off = Constraint(
            self.NONCONVEX_HEATPIPES, m.TIMESTEPS, rule=_heat_loss_rule_on_off)

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


class HeatPipeline2(Transformer):
    r"""
    Component `HeatPipeline2` to model basic characteristics of district
    heating pipelines. It is based on the GenericStorage.

    Parameters
    ----------
    nominal_storage_capacity : numeric, :math:`E_{nom}`
        Absolute nominal capacity of the storage

    invest_relation_input_capacity : numeric or None, :math:`r_{cap,in}`
        Ratio between the investment variable of the input Flow and the
        investment variable of the storage:
        :math:`\dot{E}_{in,invest} = E_{invest} \cdot r_{cap,in}`

    invest_relation_output_capacity : numeric or None, :math:`r_{cap,out}`
        Ratio between the investment variable of the output Flow and the
        investment variable of the storage:
        :math:`\dot{E}_{out,invest} = E_{invest} \cdot r_{cap,out}`

    fixed_losses_relative : numeric (iterable or scalar), :math:`\gamma(t)`
        Losses independent of state of charge between two consecutive
        timesteps relative to nominal storage capacity.
    fixed_losses_absolute : numeric (iterable or scalar), :math:`\delta(t)`
        Losses independent of state of charge and independent of
        nominal storage capacity between two consecutive timesteps.
    inflow_conversion_factor : numeric (iterable or scalar), :math:`\eta_i(t)`
        The relative conversion factor, i.e. efficiency associated with the
        inflow of the storage.
    outflow_conversion_factor : numeric (iterable or scalar), :math:`\eta_o(t)`
        see: inflow_conversion_factor
    investment : :class:`oemof.solph.options.Investment` object
        Object indicating if a nominal_value of the flow is determined by
        the optimization problem. Note: This will refer all attributes to an
        investment variable instead of to the nominal_storage_capacity. The
        nominal_storage_capacity should not be set (or set to None) if an
        investment object is used.

    Note
    ----
    The following sets, variables, constraints and objective parts are created
     * :py:class:`~oemof.solph.components.GenericStorageBlock` (if no
       Investment object present)
     * :py:class:`~oemof.solph.components.GenericInvestmentStorageBlock` (if
       Investment object present)

    Examples
    --------
    Basic usage examples of the GenericStorage with a random selection of
    attributes. See the Flow class for all Flow attributes.

    >>> from oemof import solph

    >>> my_bus = solph.Bus('my_bus')

    >>> my_storage = solph.components.GenericStorage(
    ...     label='storage',
    ...     nominal_storage_capacity=1000,
    ...     inputs={my_bus: solph.Flow(nominal_value=200, variable_costs=10)},
    ...     outputs={my_bus: solph.Flow(nominal_value=200)},
    ...     loss_rate=0.01,
    ...     initial_storage_level=0,
    ...     max_storage_level = 0.9,
    ...     inflow_conversion_factor=0.9,
    ...     outflow_conversion_factor=0.93)

    >>> my_investment_storage = solph.components.GenericStorage(
    ...     label='storage',
    ...     investment=solph.Investment(ep_costs=50),
    ...     inputs={my_bus: solph.Flow()},
    ...     outputs={my_bus: solph.Flow()},
    ...     loss_rate=0.02,
    ...     initial_storage_level=None,
    ...     invest_relation_input_capacity=1/6,
    ...     invest_relation_output_capacity=1/6,
    ...     inflow_conversion_factor=1,
    ...     outflow_conversion_factor=0.8)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nominal_storage_capacity = kwargs.get('nominal_storage_capacity')
        self.fixed_losses_relative = sequence(
            kwargs.get('fixed_losses_relative', 0))
        self.fixed_losses_absolute = sequence(
            kwargs.get('fixed_losses_absolute', 0))
        self.inflow_conversion_factor = sequence(
            kwargs.get('inflow_conversion_factor', 1))
        self.outflow_conversion_factor = sequence(
            kwargs.get('outflow_conversion_factor', 1))
        self.investment = kwargs.get('investment')
        self.invest_relation_input_capacity = kwargs.get(
            'invest_relation_input_capacity', 1)
        self.invest_relation_output_capacity = kwargs.get(
            'invest_relation_output_capacity', 1)
        self._invest_group = isinstance(self.investment, Investment)

        # Check attributes for the investment mode.
        if self._invest_group is True:
            self._check_invest_attributes()

    def _set_flows(self):
        for flow in self.inputs.values():
            if (self.invest_relation_input_capacity is not None and
                    not isinstance(flow.investment, Investment)):
                flow.investment = Investment()
        for flow in self.outputs.values():
            if (self.invest_relation_output_capacity is not None and
                    not isinstance(flow.investment, Investment)):
                flow.investment = Investment()

    def _check_invest_attributes(self):
        if self.investment and self.nominal_storage_capacity is not None:
            e1 = ("If an investment object is defined the invest variable "
                  "replaces the nominal_storage_capacity.\n Therefore the "
                  "nominal_storage_capacity should be 'None'.\n")
            raise AttributeError(e1)
        if (self.investment and
                sum(sequence(self.fixed_losses_absolute)) != 0 and
                self.investment.existing == 0 and
                self.investment.minimum == 0):
            e3 = ("With fixed_losses_absolute > 0, either investment.existing "
                  "or investment.minimum has to be non-zero.")
            raise AttributeError(e3)

        self._set_flows()

    def constraint_group(self):
        if self._invest_group is True:
            return HeatPipeline2InvestBlock
        else:
            return HeatPipeline2Block


class HeatPipeline2Block(SimpleBlock):
    r"""Storage without an :class:`.Investment` object.

    **The following sets are created:** (-> see basic sets at
    :class:`.Model` )

    STORAGES
        A set with all :class:`.Storage` objects, which do not have an
         attr:`investment` of type :class:`.Investment`.

    STORAGES_BALANCED
        A set of  all :class:`.Storage` objects, with 'balanced' attribute set
        to True.

    STORAGES_WITH_INVEST_FLOW_REL
        A set with all :class:`.Storage` objects with two investment flows
        coupled with the 'invest_relation_input_output' attribute.

    **The following variables are created:**

    storage_content
        Storage content for every storage and timestep. The value for the
        storage content at the beginning is set by the parameter `initial_storage_level`
        or not set if `initial_storage_level` is None.
        The variable of storage s and timestep t can be accessed by:
        `om.Storage.storage_content[s, t]`

    **The following constraints are created:**

    Set storage_content of last time step to one at t=0 if :attr:`balanced == True`
        .. math::
            E(t_{last}) = &E(-1)

    Storage balance :attr:`om.Storage.balance[n, t]`
        .. math:: E(t) = &E(t-1) \cdot
            (1 - \beta(t)) ^{\tau(t)/(t_u)} \\
            &- \gamma(t)\cdot E_{nom} \cdot {\tau(t)/(t_u)}\\
            &- \delta(t) \cdot {\tau(t)/(t_u)}\\
            &- \frac{\dot{E}_o(t)}{\eta_o(t)} \cdot \tau(t)
            + \dot{E}_i(t) \cdot \eta_i(t) \cdot \tau(t)

    Connect the invest variables of the input and the output flow.
        .. math::
          InvestmentFlow.invest(source(n), n) + existing = \\
          (InvestmentFlow.invest(n, target(n)) + existing) * \\
          invest\_relation\_input\_output(n) \\
          \forall n \in \textrm{INVEST\_REL\_IN\_OUT}



    =========================== ======================= =========
    symbol                      explanation             attribute
    =========================== ======================= =========
    :math:`E(t)`                energy currently stored :py:obj:`storage_content`
    :math:`E_{nom}`             nominal capacity of     :py:obj:`nominal_storage_capacity`
                                the energy storage
    :math:`c(-1)`               state before            :py:obj:`initial_storage_level`
                                initial time step
    :math:`c_{min}(t)`          minimum allowed storage :py:obj:`min_storage_level[t]`
    :math:`c_{max}(t)`          maximum allowed storage :py:obj:`max_storage_level[t]`
    :math:`\beta(t)`            fraction of lost energy :py:obj:`loss_rate[t]`
                                as share of
                                :math:`E(t)`
                                per time unit
    :math:`\gamma(t)`           fixed loss of energy    :py:obj:`fixed_losses_relative[t]`
                                relative to
                                :math:`E_{nom}` per
                                time unit
    :math:`\delta(t)`           absolute fixed loss     :py:obj:`fixed_losses_absolute[t]`
                                of energy per
                                time unit
    :math:`\dot{E}_i(t)`        energy flowing in       :py:obj:`inputs`
    :math:`\dot{E}_o(t)`        energy flowing out      :py:obj:`outputs`
    :math:`\eta_i(t)`           conversion factor       :py:obj:`inflow_conversion_factor[t]`
                                (i.e. efficiency)
                                when storing energy
    :math:`\eta_o(t)`           conversion factor when  :py:obj:`outflow_conversion_factor[t]`
                                (i.e. efficiency)
                                taking stored energy
    :math:`\tau(t)`             duration of time step
    :math:`t_u`                 time unit of losses
                                :math:`\beta(t)`,
                                :math:`\gamma(t)`
                                :math:`\delta(t)` and
                                timeincrement
                                :math:`\tau(t)`
    =========================== ======================= =========

    **The following parts of the objective function are created:**

    Nothing added to the objective function.


    """  # noqa: F401

    CONSTRAINT_GROUP = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _create(self, group=None):
        """
        Parameters
        ----------
        group : list
            List containing storage objects.
            e.g. groups=[storage1, storage2,..]
        """
        m = self.parent_block()

        if group is None:
            return None

        i = {n: [i for i in n.inputs][0] for n in group}
        o = {n: [o for o in n.outputs][0] for n in group}

        #  ************* SETS *********************************

        self.STORAGES = Set(initialize=[n for n in group])

        self.STORAGES_BALANCED = Set(initialize=[
            n for n in group if n.balanced is True])

        self.STORAGES_WITH_INVEST_FLOW_REL = Set(initialize=[
            n for n in group if n.invest_relation_input_output is not None])

        #  ************* VARIABLES *****************************

        def _storage_content_bound_rule(block, n, t):
            """Rule definition for bounds of storage_content variable of
            storage n in timestep t
            """
            bounds = (n.nominal_storage_capacity * n.min_storage_level[t],
                      n.nominal_storage_capacity * n.max_storage_level[t])
            return bounds
        self.storage_content = Var(self.STORAGES, m.TIMESTEPS,
                                   bounds=_storage_content_bound_rule)

        def _storage_init_content_bound_rule(block, n):
            return 0, n.nominal_storage_capacity

        self.init_content = Var(self.STORAGES, within=NonNegativeReals,
                                bounds=_storage_init_content_bound_rule)

        # set the initial storage content
        for n in group:
            if n.initial_storage_level is not None:
                self.init_content[n] = (n.initial_storage_level *
                                    n.nominal_storage_capacity)
                self.init_content[n].fix()

        #  ************* Constraints ***************************

        reduced_timesteps = [x for x in m.TIMESTEPS if x > 0]

        # storage balance constraint (first time step)
        def _storage_balance_first_rule(block, n):
            """Rule definition for the storage balance of every storage n for
            the first timestep.
            """
            expr = 0
            expr += block.storage_content[n, 0]
            expr += - block.init_content[n] * (
                1 - n.loss_rate[0]) ** m.timeincrement[0]
            expr += (n.fixed_losses_relative[0] * n.nominal_storage_capacity *
                     m.timeincrement[0])
            expr += n.fixed_losses_absolute[0] * m.timeincrement[0]
            expr += (- m.flow[i[n], n, 0] *
                     n.inflow_conversion_factor[0]) * m.timeincrement[0]
            expr += (m.flow[n, o[n], 0] /
                     n.outflow_conversion_factor[0]) * m.timeincrement[0]
            return expr == 0
        self.balance_first = Constraint(self.STORAGES,
                                        rule=_storage_balance_first_rule)

        # storage balance constraint (every time step but the first)
        def _storage_balance_rule(block, n, t):
            """Rule definition for the storage balance of every storage n and
            every timestep but the first (t > 0)
            """
            expr = 0
            expr += block.storage_content[n, t]
            expr += - block.storage_content[n, t-1] * (
                1 - n.loss_rate[t]) ** m.timeincrement[t]
            expr += (n.fixed_losses_relative[t] * n.nominal_storage_capacity *
                     m.timeincrement[t])
            expr += n.fixed_losses_absolute[t] * m.timeincrement[t]
            expr += (- m.flow[i[n], n, t] *
                     n.inflow_conversion_factor[t]) * m.timeincrement[t]
            expr += (m.flow[n, o[n], t] /
                     n.outflow_conversion_factor[t]) * m.timeincrement[t]
            return expr == 0
        self.balance = Constraint(self.STORAGES, reduced_timesteps,
                                  rule=_storage_balance_rule)

        def _balanced_storage_rule(block, n):
            """storage content of last time step == initial storage content
            if balanced
            """
            return (block.storage_content[n, m.TIMESTEPS[-1]]
                    == block.init_content[n])
        self.balanced_cstr = Constraint(self.STORAGES_BALANCED,
                                        rule=_balanced_storage_rule)

        def _power_coupled(block, n):
            """Rule definition for constraint to connect the input power
            and output power
            """
            expr = ((m.InvestmentFlow.invest[n, o[n]] +
                     m.flows[n, o[n]].investment.existing) *
                    n.invest_relation_input_output ==
                    (m.InvestmentFlow.invest[i[n], n] +
                     m.flows[i[n], n].investment.existing))
            return expr
        self.power_coupled = Constraint(
                self.STORAGES_WITH_INVEST_FLOW_REL, rule=_power_coupled)

    def _objective_expression(self):
        r"""Objective expression for storages with no investment.
        Note: This adds nothing as variable costs are already
        added in the Block :class:`Flow`.
        """
        if not hasattr(self, 'STORAGES'):
            return 0

        return 0


class HeatPipeline2InvestBlock(SimpleBlock):
    r"""Block for all storages with :attr:`Investment` being not None.
    See :class:`oemof.solph.options.Investment` for all parameters of the
    Investment class.

    **Variables**

    All Storages are indexed by :math:`n`, which is omitted in the following
    for the sake of convenience.
    The following variables are created as attributes of
    :attr:`om.InvestmentStorage`:

    * :math:`P_i(t)`

        Inflow of the storage
        (created in :class:`oemof.solph.models.BaseModel`).

    * :math:`P_o(t)`

        Outflow of the storage
        (created in :class:`oemof.solph.models.BaseModel`).

    * :math:`E_{invest}`

        Invested (nominal) capacity of the storage.

    * :math:`b_{invest}`

        Binary variable for the status of the investment, if
        :attr:`nonconvex` is `True`.

    **Constraints**

    The following constraints are created for all investment storages:

            Storage balance (Same as for :class:`.GenericStorageBlock`)

        .. math:: 0 =
            &- \gamma(t)\cdot (E_{exist} + E_{invest}) \cdot {\tau(t)/(t_u)}\\
            &- \delta(t) \cdot {\tau(t)/(t_u)}\\
            &- \frac{P_o(t)}{\eta_o(t)} \cdot \tau(t)
            + P_i(t) \cdot \eta_i(t) \cdot \tau(t)

    Depending on the attribute :attr:`nonconvex`, the constraints for the
    bounds of the decision variable :math:`E_{invest}` are different:\

        * :attr:`nonconvex = False`

        .. math::
            E_{invest, min} \le E_{invest} \le E_{invest, max}

        * :attr:`nonconvex = True`

        .. math::
            &
            E_{invest, min} \cdot b_{invest} \le E_{invest}\\
            &
            E_{invest} \le E_{invest, max} \cdot b_{invest}\\

    The following constraints are created depending on the attributes of
    the :class:`.components.GenericStorage`:

        * :attr:`invest_relation_input_capacity is not None`

            Connect the invest variables of the storage and the input flow:

        .. math::
            P_{i,invest} + P_{i,exist} =
            (E_{invest} + E_{exist}) \cdot r_{cap,in}

        * :attr:`invest_relation_output_capacity is not None`

            Connect the invest variables of the storage and the output flow:

        .. math::
            P_{o,invest} + P_{o,exist} =
            (E_{invest} + E_{exist}) \cdot r_{cap,out}

    **Objective function**

    The part of the objective function added by the investment storages
    also depends on whether a convex or nonconvex
    investment option is selected. The following parts of the objective
    function are created:

        * :attr:`nonconvex = False`

            .. math::
                E_{invest} \cdot c_{invest,var}

        * :attr:`nonconvex = True`

            .. math::
                E_{invest} \cdot c_{invest,var}
                + c_{invest,fix} \cdot b_{invest}\\

    The total value of all investment costs of all *InvestmentStorages*
    can be retrieved calling
    :meth:`om.GenericInvestmentStorageBlock.investment_costs.expr()`.

    .. csv-table:: List of Variables
        :header: "symbol", "attribute", "explanation"
        :widths: 1, 1, 1

        ":math:`P_i(t)`", ":attr:`flow[i[n], n, t]`", "Inflow of the storage"
        ":math:`P_o(t)`", ":attr:`flow[n, o[n], t]`", "Outlfow of the storage"
        ":math:`E_{invest}`", ":attr:`invest[n, t]`", "Invested (nominal)
        capacity of the storage"
        ":math:`b_{invest}`", ":attr:`invest_status[i, o]`", "Binary variable
        for the status of investment"
        ":math:`P_{i,invest}`", ":attr:`InvestmentFlow.invest[i[n], n]`", "
        Invested (nominal) inflow (Investmentflow)"
        ":math:`P_{o,invest}`", ":attr:`InvestmentFlow.invest[n, o[n]]`", "
        Invested (nominal) outflow (Investmentflow)"

    .. csv-table:: List of Parameters
        :header: "symbol", "attribute", "explanation"
        :widths: 1, 1, 1

        ":math:`E_{exist}`", ":py:obj:`flows[i, o].investment.existing`", "
        Existing storage capacity"
        ":math:`E_{invest,min}`", ":py:obj:`flows[i, o].investment.minimum`", "
        Minimum investment value"
        ":math:`E_{invest,max}`", ":py:obj:`flows[i, o].investment.maximum`", "
        Maximum investment value"
        ":math:`P_{i,exist}`", ":py:obj:`flows[i[n], n].investment.existing`
        ", "Existing inflow capacity"
        ":math:`P_{o,exist}`", ":py:obj:`flows[n, o[n]].investment.existing`
        ", "Existing outlfow capacity"
        ":math:`c_{invest,var}`", ":py:obj:`flows[i, o].investment.ep_costs`
        ", "Variable investment costs"
        ":math:`c_{invest,fix}`", ":py:obj:`flows[i, o].investment.offset`", "
        Fix investment costs"
        ":math:`r_{cap,in}`", ":attr:`invest_relation_input_capacity`", "
        Relation of storage capacity and nominal inflow"
        ":math:`r_{cap,out}`", ":attr:`invest_relation_output_capacity`", "
        Relation of storage capacity and nominal outflow"
        ":math:`\gamma(t)`", ":py:obj:`fixed_losses_relative[t]`", "Fixed loss
        of energy relative to :math:`E_{invest} + E_{exist}` per time unit"
        ":math:`\delta(t)`", ":py:obj:`fixed_losses_absolute[t]`", "Absolute
        fixed loss of energy per time unit"
        ":math:`\eta_i(t)`", ":py:obj:`inflow_conversion_factor[t]`", "
        Conversion factor (i.e. efficiency) when storing energy"
        ":math:`\eta_o(t)`", ":py:obj:`outflow_conversion_factor[t]`", "
        Conversion factor when (i.e. efficiency) taking stored energy"
        ":math:`\tau(t)`", "", "Duration of time step"
        ":math:`t_u`", "", "Time unit of losses :math:`\beta(t)`,
        :math:`\gamma(t)`, :math:`\delta(t)` and timeincrement :math:`\tau(t)`"

    """

    CONSTRAINT_GROUP = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _create(self, group=None):
        """
        """
        m = self.parent_block()
        if group is None:
            return None

        # ########################## SETS #####################################

        self.INVESTSTORAGES = Set(initialize=[n for n in group])

        self.CONVEX_INVESTSTORAGES = Set(initialize=[
            n for n in group if n.investment.nonconvex is False])

        self.NON_CONVEX_INVESTSTORAGES = Set(initialize=[
            n for n in group if n.investment.nonconvex is True])

        self.INVEST_REL_CAP_IN = Set(initialize=[
            n for n in group if n.invest_relation_input_capacity is not None])

        self.INVEST_REL_CAP_OUT = Set(initialize=[
            n for n in group if n.invest_relation_output_capacity is not None])

        # ######################### Variables  ################################

        def _storage_investvar_bound_rule(block, n):
            """Rule definition to bound the invested storage capacity `invest`.
            """
            if n in self.CONVEX_INVESTSTORAGES:
                return n.investment.minimum, n.investment.maximum
            elif n in self.NON_CONVEX_INVESTSTORAGES:
                return 0, n.investment.maximum

        self.invest = Var(self.INVESTSTORAGES, within=NonNegativeReals,
                          bounds=_storage_investvar_bound_rule)

        # create status variable for a non-convex investment storage
        self.invest_status = Var(self.NON_CONVEX_INVESTSTORAGES, within=Binary)

        self.heat_loss = Var(self.INVESTSTORAGES, m.TIMESTEPS,
                             within=NonNegativeReals)

        # ######################### CONSTRAINTS ###############################
        i = {n: [i for i in n.inputs][0] for n in group}
        o = {n: [o for o in n.outputs][0] for n in group}

        def _heat_loss_rule_convex(block, n, t):
            """Rule definition for constraint to connect the installed capacity
            and the heat loss
            """
            expr = 0
            expr += - block.heat_loss[n, t]
            expr += n.fixed_losses_relative[t] * self.invest[n]
            return expr == 0
        self.heat_loss_equation_convex = Constraint(
            self.CONVEX_INVESTSTORAGES, m.TIMESTEPS,
            rule=_heat_loss_rule_convex)

        def _heat_loss_rule_nonconvex(block, n, t):
            """Rule definition for constraint to connect the installed capacity
            and the heat loss
            """
            expr = 0
            expr += - block.heat_loss[n, t]
            expr += n.fixed_losses_relative[t] * self.invest[n]
            expr += n.fixed_losses_absolute[t] * self.invest_status[n]
            return expr == 0
        self.heat_loss_equation_nonconvex = Constraint(
            self.NON_CONVEX_INVESTSTORAGES, m.TIMESTEPS,
            rule=_heat_loss_rule_nonconvex)

        def _storage_balance_rule(block, n, t):
            """
            Rule definition for the storage balance of every storage n for the
            every time step but the first.
            """
            expr = 0
            expr += (- m.flow[n, o[n], t] /
                     n.outflow_conversion_factor[t])
            expr += (+ m.flow[i[n], n, t] *
                     n.inflow_conversion_factor[t])
            expr += - block.heat_loss[n, t]
            return expr == 0

        self.balance = Constraint(self.INVESTSTORAGES, m.TIMESTEPS,
                                  rule=_storage_balance_rule)

        def _storage_capacity_inflow_invest_rule(block, n):
            """Rule definition of constraint connecting the inflow
            `InvestmentFlow.invest of storage with invested capacity `invest`
            by nominal_storage_capacity__inflow_ratio
            """
            expr = ((m.InvestmentFlow.invest[i[n], n] +
                     m.flows[i[n], n].investment.existing) ==
                    (n.investment.existing + self.invest[n]) *
                    n.invest_relation_input_capacity)
            return expr
        self.storage_capacity_inflow = Constraint(
            self.INVEST_REL_CAP_IN, rule=_storage_capacity_inflow_invest_rule)

        def _storage_capacity_outflow_invest_rule(block, n):
            """Rule definition of constraint connecting outflow
            `InvestmentFlow.invest` of storage and invested capacity `invest`
            by nominal_storage_capacity__outflow_ratio
            """
            expr = ((m.InvestmentFlow.invest[n, o[n]] +
                     m.flows[n, o[n]].investment.existing) ==
                    (n.investment.existing + self.invest[n]) *
                    n.invest_relation_output_capacity)
            return expr
        self.storage_capacity_outflow = Constraint(
            self.INVEST_REL_CAP_OUT,
            rule=_storage_capacity_outflow_invest_rule)

        def maximum_invest_limit(block, n):
            """
            Constraint for the maximal investment in non convex investment
            storage.
            """
            return (n.investment.maximum * self.invest_status[n] -
                    self.invest[n]) >= 0
        self.limit_max = Constraint(
            self.NON_CONVEX_INVESTSTORAGES, rule=maximum_invest_limit)

        def smallest_invest(block, n):
            """
            Constraint for the minimal investment in non convex investment
            storage if the invest is greater than 0. So the invest variable
            can be either 0 or greater than the minimum.
            """
            return self.invest[n] - (n.investment.minimum *
                                     self.invest_status[n]) >= 0
        self.limit_min = Constraint(
            self.NON_CONVEX_INVESTSTORAGES, rule=smallest_invest)

    def _objective_expression(self):
        """Objective expression with fixed and investement costs."""
        if not hasattr(self, 'INVESTSTORAGES'):
            return 0

        investment_costs = 0

        for n in self.CONVEX_INVESTSTORAGES:
            investment_costs += (
                self.invest[n] * n.investment.ep_costs)
        for n in self.NON_CONVEX_INVESTSTORAGES:
            investment_costs += (
                    self.invest[n] * n.investment.ep_costs +
                    self.invest_status[n] * n.investment.offset)
        self.investment_costs = Expression(expr=investment_costs)

        return investment_costs

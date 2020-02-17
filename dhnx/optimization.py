from .model import OperationOptimizationModel, InvestOptimizationModel


class OemofOperationOptimizationModel(OperationOptimizationModel):
    r"""
    Implementation of an operation optimization model using oemof-solph.
    """
    def __init__(self, thermal_network):
        super().__init__(thermal_network)

    def setup(self):
        pass

    def solve(self):
        pass

    def get_results(self):
        pass


class OemofInvestOptimizationModel(InvestOptimizationModel):
    r"""
    Implementation of an invest optimization model using oemof-solph.
    """
    def __init__(self, thermal_network):
        super().__init__(thermal_network)

    def setup(self):
        pass

    def solve(self):
        pass

    def get_results(self):
        pass


def optimize_operation(thermal_network):
    r"""
    Takes a thermal network and returns the result of
    the operational optimization.

    Parameters
    ----------
    thermal_network

    Returns
    -------
    results : dict
    """
    model = OemofOperationOptimizationModel(thermal_network)

    model.solve()

    results = model.get_results()

    return results


def optimize_investment(thermal_network):
    r"""
    Takes a thermal network and returns the result of
    the investment optimization.

    Parameters
    ----------
    thermal_network

    Returns
    -------
    results : dict
    """
    model = OemofInvestOptimizationModel(thermal_network)

    model.solve()

    results = model.get_results()

    return results

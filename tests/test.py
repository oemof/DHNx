import filecmp
import pytest

import district_heating_simulation as dhs


def test_import_export_csv(tmpdir):
    dir_import = '_files/network_import'
    dir_export = tmpdir

    network = dhs.network.ThermalNetwork()
    network = network.load_from_csv(dir_import)

    network.save_to_csv(dir_export)

    files = ['consumers.csv', 'producers.csv', 'splits', 'edges.csv']
    is_same = filecmp.cmpfiles(dir_import, dir_export, files)

    assert is_same


def test_operation_optimization():
    dir_import = '_files/network_import'
    dir_problem = '_files/problem_operation'

    network = dhs.network.ThermalNetwork()
    network.load_from_csv(dir_import)

    problem = dhs.input_output.load_problem(dir_problem)

    model = dhs.models.OperationOptimizationModel(network, problem)

    results = model.solve()
    default_results = None

    assert results == default_results

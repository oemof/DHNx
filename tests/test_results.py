import os

import dhnx

from . import helpers

# define paths
tests_path = os.path.abspath(os.path.dirname(__file__))

tmp_dir = helpers.extend_basic_path('tmp')


def test_tree_simulation():

    input_data = os.path.join(
        tests_path,
        '_files',
        'tree_network_import')

    expected_results = os.path.join(
        tests_path,
        '_files',
        'tree_network_sim_expected_results',
        'sequences'
    )

    results_path = os.path.join(
        tmp_dir,
        'tree_results'
    )

    # Initialize thermal network
    tnw = dhnx.network.ThermalNetwork()

    # Load data from csv
    tnw.from_csv_folder(input_data)

    # Create simulation model
    tnw.simulate(results_dir=results_path)

    # compare with expected results
    helpers.check_if_csv_dirs_equal(results_path, expected_results)

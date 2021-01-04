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
    # Workaround since the benchmark data was created in a different way:
    # Ignore differences in columns and index.
    helpers.check_if_csv_dirs_equal(results_path, expected_results, check_arrays=True)


def test_tree_simulation_reverse_pipe_dir():

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
        'tree_results_reversed_pipe'
    )

    # Initialize thermal network
    tnw = dhnx.network.ThermalNetwork()

    # Load data from csv
    tnw.from_csv_folder(input_data)

    # Swap direction of first pipe
    tnw.components.pipes.loc[0, ['from_node', 'to_node']] = \
        tnw.components.pipes.loc[0, ['to_node', 'from_node']].values

    # Create simulation model
    tnw.simulate(results_dir=results_path)

    # compare with expected results
    # Workaround since the benchmark data was created in a different way:
    # Ignore differences in columns and index.
    helpers.check_if_csv_dirs_equal(results_path, expected_results, check_arrays=True)

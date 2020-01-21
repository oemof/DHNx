import os
import pandas as pd

import district_heating_simulation as dhs


def check_if_csv_files_equal(csv_file_a, csv_file_b):
    df1 = pd.read_csv(csv_file_a)
    df2 = pd.read_csv(csv_file_b)

    return df1.equals(df2)


def check_if_csv_dirs_equal(dir_a, dir_b):
    files_a = [os.path.join(dir_a, f) for f in os.listdir(dir_a)]
    files_b = [os.path.join(dir_b, f) for f in os.listdir(dir_b)]
    files_a.sort()
    files_b.sort()

    for file_a, file_b in zip(files_a, files_b):
        assert check_if_csv_files_equal(file_a, file_b)


def test_import_export_csv(tmpdir):
    dir_import = '_files/network_import'
    dir_export = os.path.join(tmpdir, 'network_export')

    network = dhs.network.ThermalNetwork()
    network = network.load_from_csv(dir_import)

    network.save_to_csv(dir_export)

    check_if_csv_dirs_equal(dir_import, dir_export)

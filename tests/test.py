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

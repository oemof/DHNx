import os

import pandas as pd

from .input_output import CSVNetworkImporter, CSVNetworkExporter, load_component_attrs
from .graph import thermal_network_to_nx_graph


dir_name = os.path.dirname(__file__)

available_components = pd.read_csv(os.path.join(dir_name, 'components.csv'), index_col=0)

component_attrs = load_component_attrs(os.path.join(dir_name, 'component_attrs'),
                                       available_components)


class ThermalNetwork():
    r"""
    Class representing thermal (heating/cooling) networks.

    Parameters
    ----------

    Examples
    --------
    >>> from dhnx import ThermalNetwork
    >>> tnw = ThermalNetwork('csv_folder')
    >>> tnw.is_consistent()
    True
    """
    def __init__(self, dirname=None):

        self.available_components = available_components
        self.component_attrs = component_attrs
        self.components = {key: pd.DataFrame() for key in available_components.list_name}
        self.sequences = {}
        self.results = None
        self.graph = None

        if dirname is not None:
            try:
                self.from_csv_folder(dirname)

            except ImportError:
                print('Failed to import file.')

    def from_csv_folder(self, dirname):
        importer = CSVNetworkImporter(self, dirname)

        self = importer.load()

        return self

    def to_csv_folder(self, dirname):
        exporter = CSVNetworkExporter(self, dirname)

        self = exporter.save()

    def to_nx_graph(self):
        nx_graph = thermal_network_to_nx_graph(self)

        return nx_graph

    def add(self, class_name, id, **kwargs):
        r"""
        Adds a row with id to the component DataFrame specified by class_name.

        Parameters
        ----------
        class_name
        id
        kwargs
        """
        assert class_name in available_components.index,\
            "Component class {} is not within the available components."

        list_name = available_components.loc[class_name].list_name

        assert id not in self.components[list_name].index,\
            f"There is already a component with the id {id}."

        for key, value in kwargs.items():
            self.components[list_name].loc[id, key] = value

    def remove(self, class_name, id):
        r"""
        Removes the row with id from the component DataFrame specified by class_name.

        Parameters
        ----------
        class_name : str
            Name of the component class
        id : int
            id of the component to remove
        """
        assert class_name in available_components.index,\
            "Component class '{}' is not within the available_components."

        list_name = available_components.loc[class_name].list_name

        assert id in self.components[list_name].index,\
            f"There is no component with the id {id}."

        self.components[list_name].drop(id, inplace=True)

    def is_consistent(self):
        pass

    def reproject(self, crs):
        pass

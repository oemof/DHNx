import os
import pandas as pd


class NetworkImporter():
    r"""
    Generic Importer object for network.ThermalNetwork
    """
    def __init__(self, thermal_network, basedir):
        thermal_network.is_consistent()
        self.thermal_network = thermal_network
        self.basedir = basedir

    def load(self):
        pass


class NetworkExporter():
    r"""
    Generic Exporter object for network.ThermalNetwork
    """
    def __init__(self, thermal_network, basedir):
        thermal_network.is_consistent()
        self.thermal_network = thermal_network
        self.basedir = basedir

    def save(self):
        pass


class CSVNetworkImporter(NetworkImporter):
    r"""
    Imports thermal networks from directory with csv-files.
    """
    def __init__(self, thermal_network, basedir):
        super().__init__(thermal_network, basedir)

    def load_component_table(self, name):
        component_table = pd.read_csv(os.path.join(self.basedir, name), index_col=0)

        return component_table

    def load(self):
        for table_name in os.listdir(self.basedir):

            list_name = os.path.splitext(table_name)[0]

            if list_name not in self.thermal_network.available_components.list_name.values:
                raise KeyError(f"Component '{list_name}' is not part of the available components.")

            self.thermal_network.components[list_name] = self.load_component_table(table_name)

        return self.thermal_network


class CSVNetworkExporter(NetworkExporter):
    r"""
    Exports thermal networks to directory with csv-files.
    """
    def __init__(self, thermal_network, basedir):
        super().__init__(thermal_network, basedir)
        if not os.path.exists(self.basedir):
            os.mkdir(self.basedir)

    def save_component_table(self, component_table, name):
        component_table.to_csv(os.path.join(self.basedir, name))

    def save(self):
        for component, component_table in self.thermal_network.components.items():
            filename = component + '.csv'
            self.save_component_table(component_table, filename)


class OSMNetworkImporter(NetworkImporter):
    r"""
    Imports thermal networks from OSM data.
    """
    def __init__(self):
        pass


class GDFNetworkExporter(NetworkExporter):
    r"""
    Exports thermal networks to geopandas.GeoDataFrame.
    """
    def __init__(self):
        pass

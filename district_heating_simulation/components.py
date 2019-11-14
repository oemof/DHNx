
import os
from typing import List
from dataclasses import dataclass, field
from dataclass_csv import DataclassReader  # See https://github.com/dfurtado/dataclass-csv


COMPONENT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples/berlin_example/berlin_data")


@dataclass
class Node:
    node_id: int
    lat: float
    lon: float

    def __post_init__(self):  # See https://docs.python.org/3/library/dataclasses.html#post-init-processing
        assert -90 < self.lat < 90
        assert -180 < self.lon < 180


@dataclass
class NodeList:
    nodes: List[Node] = field(default_factory=list)

    def load_components_from_csv(self, filename, component_class):
        with open(os.path.join(COMPONENT_FOLDER, filename)) as f:
            reader = DataclassReader(f, component_class)
            self.nodes += [node for node in reader]


@dataclass
class Producer(Node):
    nominal_value: float


@dataclass
class Heatpump(Producer):
    min_temp: float


if __name__ == '__main__':
    node_list = NodeList()
    node_list.load_components_from_csv('heatpump.csv', Heatpump)
    node_list.load_components_from_csv('producers.csv', Producer)
    print(node_list)



from .move import MoveNeighborhoodGenerator
from .or_opt import OrOptGenerator
from .cross import CrossGenerator, Cross3Generator
from .swap import Swap11Generator, Swap22Generator, Swap111Generator

neighborhood_generators = [
    MoveNeighborhoodGenerator,  # OK
    Swap11Generator,  # OK
    Swap111Generator,  # OK
    Swap22Generator,  # OK
    CrossGenerator,  # OK
    OrOptGenerator,  # OK~
    Cross3Generator,  # OK
]
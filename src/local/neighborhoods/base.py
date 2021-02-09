import sys
from itertools import product
from copy import deepcopy
import multiprocessing as mp
from functools import partial

from ..models import Solution, Route


class BaseNeighborhoodGenerator:

    def __init__(self, solution, dim=2):
        self.solution_routes = {i: r for i, r in enumerate(solution.routes)}
        self.dim = dim
        try:
            self.routes_generators = self._get_routes_generators()
        except NotImplementedError:
            self.routes_generators = None

    def _get_routes_generators(self):
        # implement in child class
        raise NotImplementedError

    def _neighbors_generation_method(self, routes_indices, G, Q):
        # implement in child class
        raise NotImplementedError

    def _generate_combinations(self):
        # default: cartesian product between original solution routes
        routes_keys = list(self.solution_routes.keys())
        return product(*((routes_keys, ) * self.dim))

    def _generate_neighbors_internal(self, G, Q, routes_indices):
        neighborhood = {}
        # generate new routes
        new_routes_list = self._neighbors_generation_method(routes_indices, G, Q)
        for new_routes in new_routes_list:
            # build neighbor solution
            neighbor_routes = deepcopy(self.solution_routes)
            for route_nodes, original_idx in zip(new_routes, routes_indices):
                # if route is None, the route has been removed
                if route_nodes is None:
                    del neighbor_routes[original_idx]
                else:
                    neighbor_routes[original_idx] = Route(G, route_nodes, Q)
            neighbor = Solution(G, list(neighbor_routes.values()), Q)
            # add solution to neighborhood (overwrite if already present)
            neighborhood[neighbor.as_hash()] = neighbor
        return neighborhood

    def generate_neighbors(self, G, Q):
        routes_combinations = list(self._generate_combinations())
        debug_mode = sys.gettrace() is not None
        if debug_mode:
            # single processing (for debug reasons)
            neighborhood = {}
            for routes_indices in routes_combinations:
                neighbors = self._generate_neighbors_internal(
                    G, Q, routes_indices)
                for sol_hash, sol in neighbors.items():
                    neighborhood[sol_hash] = sol
        else:
            # generate partial neighborhoods using multiprocessing
            with mp.Pool(mp.cpu_count()-1) as pool:
                partial_f = partial(self._generate_neighbors_internal, G, Q)
                partial_nbh = pool.map(partial_f, routes_combinations)
            # merge partial neighborhoods into a single one
            neighborhood = {}
            for p_nbh in partial_nbh:
                for sol_hash, sol in p_nbh.items():
                    neighborhood[sol_hash] = sol
        return list(neighborhood.values())

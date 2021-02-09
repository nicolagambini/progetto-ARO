from itertools import product, combinations

from .base import BaseNeighborhoodGenerator
from .property_checks import check_property_3
from ..models import Route


def cross_nodes_if_feasible(p_nodes_partial, r_nodes_partial, G, Q):
    if check_property_3(Q,
                        Route(G, p_nodes_partial+[0], Q),
                        Route(G, [0]+r_nodes_partial, Q)):
        return p_nodes_partial + r_nodes_partial
    return None


def cross(cross_info, G, Q):
    new_routes = []
    if len(cross_info) == 2:
        # two routes cross
        (p_nodes, p_pos), (r_nodes, r_pos) = cross_info
        # merge routes, if possible
        new_p = cross_nodes_if_feasible(p_nodes[:p_pos], r_nodes[r_pos:], G, Q)
        new_r = cross_nodes_if_feasible(r_nodes[:r_pos], p_nodes[p_pos:], G, Q)
        # append the results to the return list
        if all([n is not None for n in [new_p, new_r]]):
            new_routes.append([new_p, new_r])
    elif len(cross_info) == 3:
        # three routes cross
        (p_nodes, p_pos), (r_nodes, r_pos), (s_nodes, s_pos) = cross_info
        # merge routes, if possible (1st variant)
        new_p = cross_nodes_if_feasible(p_nodes[:p_pos], r_nodes[r_pos:], G, Q)
        new_r = cross_nodes_if_feasible(r_nodes[:r_pos], s_nodes[s_pos:], G, Q)
        new_s = cross_nodes_if_feasible(s_nodes[:s_pos], p_nodes[p_pos:], G, Q)
        if all([n is not None for n in [new_p, new_r, new_s]]):
            new_routes.append([new_p, new_r, new_s])
        # merge routes, if possible (2nd variant)
        new_p = cross_nodes_if_feasible(p_nodes[:p_pos], s_nodes[s_pos:], G, Q)
        new_r = cross_nodes_if_feasible(r_nodes[:r_pos], p_nodes[p_pos:], G, Q)
        new_s = cross_nodes_if_feasible(s_nodes[:s_pos], r_nodes[r_pos:], G, Q)
        if all([n is not None for n in [new_p, new_r, new_s]]):
            new_routes.append([new_p, new_r, new_s])
    else:
        raise ValueError("Unhandled number of roads")
    # normalize result and return it
    result = []
    for routes_tuple in new_routes:
        result.append([r if (len(r) > 2) else None
                       for r in routes_tuple])
    return result


class CrossGenericGenerator(BaseNeighborhoodGenerator):

    def __init__(self, solution, k=None):
        assert k > 1
        self.k = k
        super().__init__(solution)

    def _generate_combinations(self):
        # combine routes longer than 3 stations
        r_keys = [i for i, r in self.solution_routes.items() if len(r.nodes) > 3]
        return combinations(r_keys, self.k)

    def _get_routes_generators(self):
        rg = {}
        for route_idx, r in self.solution_routes.items():
            if len(r.nodes) <= 3:
                continue
            if route_idx not in rg:
                rg[route_idx] = []
            for i in range(1, len(r.nodes)):
                rg[route_idx].append((r, i))
        return rg

    def _neighbors_generation_method(self, routes_indices, G, Q):
        generators = [self.routes_generators[idx] for idx in routes_indices]
        # get all possible crossings
        results = []
        for cross_info in product(*generators):
            # skip if position of all route is 1 (it would have no effect)
            if all([pos == 1 for _, pos in cross_info]):
                continue
            result = cross([(r.as_list_of_nodes_indices(), pos)
                            for r, pos in cross_info], G, Q)
            results.extend(result)
        return results


class CrossGenerator(CrossGenericGenerator):

    def __init__(self, solution):
        super().__init__(solution, 2)


class Cross3Generator(CrossGenericGenerator):

    def __init__(self, solution):
        super().__init__(solution, 3)

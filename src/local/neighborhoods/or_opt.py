from itertools import product

from .base import BaseNeighborhoodGenerator
from ..constructive_methods import routes_load_windows_overlap
from ..models import Route


def move_if_feasible(single_route, src_a, src_b, src_c, dst_a, dst_b, G, Q):
    result = []
    # STEP 1: check source route merge (src_a+src_c) feasibility. It only makes
    # sense if applied on two different routes (skip if single_route)
    if not single_route:
        if len(src_a+src_c) <= 2:  # delete src_route
            result.append(None)
        else:
            if len(src_a) > 1 and len(src_c) > 1:
                is_overlap = routes_load_windows_overlap(Route(G, src_a+[0], Q),
                                                         Route(G, [0]+src_c, Q),
                                                         Q,
                                                         p_node_idx=len(src_a)-2,
                                                         r_node_idx=1)
                if not is_overlap:
                    return None
            # append the merge to the results list
            merge_nodes = src_a + src_c
            result.append(merge_nodes)
    # STEP 2: check source if route build from fragment (src_b) is feasible
    fragment_route = Route(G, [0]+src_b+[0], Q)
    for i in range(1, len(src_b)):
        f_a, f_b = Route(G, [0]+src_b[:i]+[0], Q),\
                   Route(G, [0]+src_b[i:]+[0], Q)
        if not routes_load_windows_overlap(f_a, f_b, Q, i, 1):
            return None
    # STEP 3: check if merge between dst_a+fragment is feasible (first half)
    if len(dst_a) > 1 and not routes_load_windows_overlap(Route(G, dst_a+[0], Q),
                                                          fragment_route,
                                                          Q, len(dst_a)-1, 1):
        return None
    first_half = Route(G, dst_a+src_b+[0], Q)
    # STEP 4: check if merge between first_half+dst_b is feasible
    if len(dst_b) > 1 and not routes_load_windows_overlap(first_half,
                                                          Route(G, [0]+dst_b, Q),
                                                          Q, len(first_half.nodes)-2, 1):
        return None
    # append merge to the results list
    merge_nodes = dst_a + src_b + dst_b
    result.append(merge_nodes)
    return result


def move_stations(src_nodes, dst_nodes, src_interval, dst_pos, G, Q):
    a, b = src_interval
    is_single_route = (src_nodes == dst_nodes)
    if is_single_route:
        offset = (b-a) if b < dst_pos else 0
        dst_nodes = dst_nodes[:a] + dst_nodes[b+1:]
        dst_pos -= offset
        """offset = max(0, b-dst_pos) if b < dst_pos else 0
        interval = src_nodes[a:b+1]
        new_r = src_nodes[:dst_pos] + interval + src_nodes[dst_pos:]
        new_r = new_r[:a+offset] + new_r[b+1+offset:]
        return [new_r]
   else:
        new_r1 = src_nodes[:a] + src_nodes[b+1:]
        new_r2 = dst_nodes[:dst_pos] + src_nodes[a:b+1] + dst_nodes[dst_pos:]
        if len(new_r1) <= 2:
            new_r1 = None
        return [new_r1, new_r2]"""
    return move_if_feasible(is_single_route,
                            src_nodes[:a], src_nodes[a:b+1], src_nodes[b+1:],
                            dst_nodes[:dst_pos], dst_nodes[dst_pos:], G, Q)


class OrOptGenerator(BaseNeighborhoodGenerator):

    def __init__(self, solution, k=35):
        self.k = k  # maximum length of segments to swap
        super().__init__(solution)

    def _get_routes_generators(self):
        rg = {}
        for route_idx, r in self.solution_routes.items():
            if route_idx not in rg:
                rg[route_idx] = {
                    "src": [(r, (i, j))
                            for i in range(1, len(r.nodes)-2)
                            for j in range(i+1, len(r.nodes)-1)
                            if j-i < self.k],
                    "dst": [(r, i) for i in range(1, len(r.nodes)-1)]
                }
        return rg

    def _neighbors_generation_method(self, routes_indices, G, Q):
        p_idx, r_idx = routes_indices
        p_generators = self.routes_generators[p_idx]["src"]
        r_generators = self.routes_generators[r_idx]["dst"]
        # get all possible crossings
        results = []
        for cross_info in product(p_generators, r_generators):
            (src_route, (src_pos1, src_pos2)), (dst_route, dst_pos) = cross_info
            # skip if trying to move the selected node in the original position
            if p_idx == r_idx and src_pos1 <= dst_pos <= src_pos2+1:
                continue
            result = move_stations(src_route.as_list_of_nodes_indices(),
                                   dst_route.as_list_of_nodes_indices(),
                                   src_interval=(src_pos1, src_pos2),
                                   dst_pos=dst_pos,
                                   G=G, Q=Q)
            results.append(result)
        return [r for r in results if r is not None]

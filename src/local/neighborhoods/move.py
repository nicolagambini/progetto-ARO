from itertools import chain, product

from .base import BaseNeighborhoodGenerator
from .property_checks import *


def is_move_feasible(Q, p, r, p_pos, r_pos):
    if check_property_1(p, r, p_pos) and \
       check_property_2a_2b(p, r, p_pos) and \
       check_property_4b(Q, p, p_pos) and \
       check_property_4c(Q, p, r, p_pos, r_pos):
        return True
    return False


def move_station(src_route_nodes, dst_route_nodes, src_pos, dst_pos):
    # return empty list if no moves can be done (e.g. if src=dst=[0,1,0])
    is_single_route = (src_route_nodes == dst_route_nodes)
    if is_single_route and len(src_route_nodes) == 3:
        return []
    result = []
    # apply a move operation on routes
    node_to_move = src_route_nodes.pop(src_pos)
    if is_single_route:
        src_route_nodes = src_route_nodes[:dst_pos] \
                          + [node_to_move] \
                          + src_route_nodes[dst_pos:]
    else:
        dst_route_nodes = dst_route_nodes[:dst_pos] + \
                          [node_to_move] + \
                          dst_route_nodes[dst_pos:]
        result.append(dst_route_nodes)
    result.append(src_route_nodes if len(src_route_nodes) > 2 else None)
    return list(reversed(result))


def apply_move(move, Q):
    (src_route, src_pos), (dst_route, dst_pos) = move
    # skip if trying to move same node in same position
    if src_route.as_hash() == dst_route.as_hash() and src_pos == dst_pos:
        return None
    # check move feasibility based on properties 1/2a/2b/4b/4c
    if not is_move_feasible(Q, src_route, dst_route, src_pos, dst_pos):
        return None
    # define new route(s)
    src_route_nodes = src_route.as_list_of_nodes_indices()
    dst_route_nodes = dst_route.as_list_of_nodes_indices()
    return move_station(src_route_nodes, dst_route_nodes, src_pos, dst_pos)


class MoveNeighborhoodGenerator(BaseNeighborhoodGenerator):

    def _get_routes_generators(self):
        return {i: [(r, j) for j in range(1, len(r.nodes)-1)]
                for i, r in self.solution_routes.items()}

    def _neighbors_generation_method(self, routes_indices, G, Q):
        p_idx, r_idx = routes_indices
        p_generator = self.routes_generators[p_idx]
        r_generator = self.routes_generators[r_idx]

        if p_idx == r_idx:
            moves = product(p_generator, r_generator)
        else:
            moves = chain(product(p_generator, r_generator),
                          product(r_generator, p_generator))

        results = []
        for m in moves:
            results.append(apply_move(m, Q))
        return [r for r in results if r is not None]

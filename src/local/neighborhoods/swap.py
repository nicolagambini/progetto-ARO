from itertools import combinations, product
from copy import deepcopy, copy
from local.neighborhoods.base import BaseNeighborhoodGenerator
from .property_checks import *


def is_single_swap_feasible(Q, p, r, p_pos, r_pos):
    if check_property_2c(p, r, p_pos, r_pos) and \
       check_property_2d(p, r, p_pos, r_pos) and \
       check_property_4d(Q, p, r, p_pos, r_pos):
        return True
    return False


def is_double_swap_feasible(G, Q, p, r, p_pos, r_pos):
    p_nodes = p.as_list_of_nodes_indices()
    r_nodes = r.as_list_of_nodes_indices()

    # check fragments feasibility
    p_fragment = p_nodes[p_pos:p_pos+2]
    r_fragment = r_nodes[r_pos:r_pos+2]
    for f in [p_fragment, r_fragment]:
        f_a, f_b = Route(G, [0]+f[:1]+[0], Q), Route(G, [0]+f[-1:]+[0], Q)
        if not routes_load_windows_overlap(f_a, f_b, Q, 1, 1):
            return False

    single_route = (p_nodes == r_nodes)
    if single_route:
        # sort interval start indices
        a, b = min(p_pos, r_pos), max(p_pos, r_pos)
        # define fragments for feasibility check
        fragments = p_nodes[:a], p_nodes[b:b+2], p_nodes[a+2:b], \
                    p_nodes[a:a+2], p_nodes[b+2:]
        # iterate fragments for feasibility check
        partial = copy(fragments[0])
        for f in fragments[1:]:
            if len(partial) <= 1 or (len(f) == 0 or f[0] == 0):
                partial += f
                continue
            f_a, f_b = Route(G, partial+[0], Q), Route(G, [0]+f+[0], Q)
            if not routes_load_windows_overlap(f_a, f_b, Q, len(partial)-1, 1):
                return False
            partial += f
        x = 1
    else:
        # STEP 1: check p->r feasibility (ppXXp)
        # 1) ppYY è feasible?
        if p_pos > 1:
            f_a, f_b = Route(G, p_nodes[:p_pos]+[0], Q),\
                       Route(G, [0]+r_nodes[r_pos:r_pos+2]+[0], Q)
            if not routes_load_windows_overlap(f_a, f_b, Q, p_pos-1, 1):
                return False
        # 2) ppYYp è feasible?
        if p_pos + 2 < len(p_nodes) - 1:
            f_a, f_b = Route(G, p_nodes[:p_pos]+r_nodes[r_pos:r_pos+2]+[0], Q),\
                       Route(G, [0]+p_nodes[p_pos+2:], Q)
            if not routes_load_windows_overlap(f_a, f_b, Q, p_pos+1, 1):
                return False
        # STEP 2: check r->p feasibility (rYYrrr)
        # 1) rXX è feasible?
        if r_pos > 1:
            f_a, f_b = Route(G, r_nodes[:r_pos]+[0], Q), \
                       Route(G, [0]+p_nodes[p_pos:p_pos+2]+[0], Q)
            if not routes_load_windows_overlap(f_a, f_b, Q, r_pos-1, 1):
                return False
        # 2) rXXrrr è feasible?
        if r_pos + 2 < len(r_nodes) - 1:
            f_a, f_b = Route(G, r_nodes[:r_pos]+p_nodes[p_pos:p_pos+2]+[0], Q),\
                       Route(G, [0]+r_nodes[r_pos+2:], Q)
            if not routes_load_windows_overlap(f_a, f_b, Q, r_pos+1, 1):
                return False
    return True


def swap_routes_parts(p_nodes, r_nodes, p_pos, r_pos, k):
    if p_nodes == r_nodes:
        h = p_nodes[p_pos:p_pos+k]
        p_nodes[p_pos:p_pos+k] = p_nodes[r_pos:r_pos+k]
        p_nodes[r_pos:r_pos+k] = h
        return [p_nodes]
    r1 = p_nodes[:p_pos] + r_nodes[r_pos:r_pos+k] + p_nodes[p_pos+k:]
    r2 = r_nodes[:r_pos] + p_nodes[p_pos:p_pos+k] + r_nodes[r_pos+k:]
    return [r1, r2]


def swap_nodes_if_feasible(p, r, p_pos, r_pos, G, Q):
    if not is_single_swap_feasible(Q, p, r, p_pos, r_pos):
        return None
    p_nodes = p.as_list_of_nodes_indices()
    r_nodes = r.as_list_of_nodes_indices()
    p_nodes[p_pos], r_nodes[r_pos] = r_nodes[r_pos], p_nodes[p_pos]
    return Route(G, p_nodes, Q), Route(G, r_nodes, Q)


def rotate_stations(grouped_rotation_components, direction, G, Q):
    assert 0 < len(grouped_rotation_components) <= 3
    assert direction in ["right", "left"]
    # direction==right: v1-->v2;v2-->v3;v3-->v1
    # direction==left: v3-->v1;v3-->v2;v2-->v1

    # sort grouped rotation components by the number of positions per
    # route, in a descendant fashion
    grc_list = [(route_idx, (route_info["route"], route_info["positions"]))
                for route_idx, route_info in grouped_rotation_components.items()]
    grc_list.sort(key=lambda x: len(x[1][1]), reverse=True)

    if len(grouped_rotation_components) == 3:
        # CASE 1: THREE DIFFERENT ROUTES ***************************************
        (r1_idx, (r1_route, (r1_pos, ))), (r2_idx, (r2_route, (r2_pos, ))), \
            (r3_idx, (r3_route, (r3_pos, ))) = grc_list
        if direction == "right":
            # first swap: r1<->r2
            first_swap = swap_nodes_if_feasible(r1_route, r2_route, r1_pos, r2_pos, G, Q)
            if first_swap is None:
                return None
            r1_route, r2_route = first_swap
            # second swap: r1<->r3
            second_swap = swap_nodes_if_feasible(r1_route, r3_route, r1_pos, r3_pos, G, Q)
            if second_swap is None:
                return None
            r1_route, r3_route = second_swap
        else:  # left
            # first swap: r1<->r3
            first_swap = swap_nodes_if_feasible(r1_route, r3_route, r1_pos, r3_pos, G, Q)
            if first_swap is None:
                return None
            r1_route, r3_route = first_swap
            # second swap: r1<->r2
            second_swap = swap_nodes_if_feasible(r1_route, r2_route, r1_pos, r2_pos, G, Q)
            if second_swap is None:
                return None
            r1_route, r2_route = second_swap
        return {
            r1_idx: r1_route.as_list_of_nodes_indices(),
            r2_idx: r2_route.as_list_of_nodes_indices(),
            r3_idx: r3_route.as_list_of_nodes_indices(),
        }
    elif len(grouped_rotation_components) == 2:
        # CASE 2: TWO ROUTES, ONE CONTAINING TWO TARGET POSITIONS **************
        (r1_idx, (r1_route, (r1_p1, r1_p2))), (r2_idx, (r2_route, (r2_p1, ))) =\
            grc_list
        if direction == "right":
            # first swap: r1_p1<->r1_p2
            first_swap = swap_nodes_if_feasible(r1_route, r1_route, r1_p1, r1_p2, G, Q)
            if first_swap is None:
                return None
            r1_route, _ = first_swap
            # second swap: r1_p1<->r2_p1
            second_swap = swap_nodes_if_feasible(r1_route, r2_route, r1_p1, r2_p1, G, Q)
            if second_swap is None:
                return None
            r1_route, r2_route = second_swap
        else:  # left
            # first swap: r1_p1<->r2_p1
            first_swap = swap_nodes_if_feasible(r1_route, r2_route, r1_p1, r2_p1, G, Q)
            if first_swap is None:
                return None
            r1_route, r2_route = first_swap
            # second swap: r1_p1<->r1_p2
            second_swap = swap_nodes_if_feasible(r1_route, r1_route, r1_p1, r1_p2, G, Q)
            if second_swap is None:
                return None
            r1_route, _ = second_swap
        return {
            r1_idx: r1_route.as_list_of_nodes_indices(),
            r2_idx: r2_route.as_list_of_nodes_indices()
        }
    else:
        # CASE 3: SINGLE ROUTE ROTATION ****************************************
        route_idx, (route, (p1, p2, p3)) = grc_list.pop()
        if direction == "right":
            # first swap: p1<->p2
            first_swap = swap_nodes_if_feasible(route, route, p1, p2, G, Q)
            if first_swap is None:
                return None
            route, _ = first_swap
            # second swap: p1<->p3
            second_swap = swap_nodes_if_feasible(route, route, p1, p3, G, Q)
            if second_swap is None:
                return None
            route, _ = second_swap
        else:  # left
            # first swap: p1<->p3
            first_swap = swap_nodes_if_feasible(route, route, p1, p3, G, Q)
            if first_swap is None:
                return None
            route, _ = first_swap
            # second swap: p1<->p3
            second_swap = swap_nodes_if_feasible(route, route, p1, p2, G, Q)
            if second_swap is None:
                return None
            route, _ = second_swap
        return {
            route_idx: route.as_list_of_nodes_indices()
        }


class SwapGenerator(BaseNeighborhoodGenerator):

    def __init__(self, solution, k=None):
        self.k = k
        super().__init__(solution)

    def _get_routes_generators(self):
        return {i: [(r, j) for j in range(1, len(r.nodes)-self.k)]
                for i, r in self.solution_routes.items()}

    def _neighbors_generation_method(self, routes_indices, G, Q):
        if self.k is None:
            return []
        p_idx, r_idx = routes_indices
        p_generator = self.routes_generators[p_idx]
        r_generator = self.routes_generators[r_idx]
        # get all possible swaps
        swaps = combinations(p_generator, 2) if p_idx == r_idx else \
            product(p_generator, r_generator)
        results = []
        for (src_route, src_pos), (dst_route, dst_pos) in swaps:
            # skip if swap in same route and in same position
            if p_idx == r_idx and abs(src_pos - dst_pos) < self.k:
                continue
            # check feasibility
            if self.k == 1 and not is_single_swap_feasible(Q, src_route, dst_route, src_pos, dst_pos):
                continue
            elif self.k == 2 and not is_double_swap_feasible(G, Q, src_route, dst_route, src_pos, dst_pos):
                continue
            # define new route(s)
            src_route_nodes = src_route.as_list_of_nodes_indices()
            dst_route_nodes = dst_route.as_list_of_nodes_indices()
            swap_results = swap_routes_parts(src_route_nodes,
                                             dst_route_nodes,
                                             src_pos,
                                             dst_pos,
                                             self.k)
            results.append(swap_results)
        return results


class Swap11Generator(SwapGenerator):

    def __init__(self, solution):
        super().__init__(solution, 1)


class Swap22Generator(SwapGenerator):

    def __init__(self, solution):
        super().__init__(solution, 2)


class Swap111Generator(BaseNeighborhoodGenerator):

    def __init__(self, solution):
        super().__init__(solution, dim=3)

    def _get_routes_generators(self):
        return {route_idx: [(route_idx, pos) for pos in range(1, len(r.nodes)-1)]
                for route_idx, r in self.solution_routes.items()}

    def _neighbors_generation_method(self, routes_indices, G, Q):
        p_idx, r_idx, s_idx = routes_indices
        p_generator = self.routes_generators[p_idx]
        r_generator = self.routes_generators[r_idx]
        s_generator = self.routes_generators[s_idx]

        rotations = product(p_generator, r_generator, s_generator)
        results = []
        for rotation_components in rotations:
            # skip if any of the components is duplicate (same route, same pos)
            rotation_set = set(rotation_components)
            if len(rotation_set) < 3:
                continue
            # define new route(s)
            grouped_rotation_components = {}
            for route_idx, pos in rotation_components:
                # define group as ((<route_idx>, <route_nodes>), positions)
                if route_idx not in grouped_rotation_components:
                    grouped_rotation_components[route_idx] = {
                        "route": deepcopy(self.solution_routes[route_idx]),
                        "positions": []
                    }
                grouped_rotation_components[route_idx]["positions"].append(pos)
            for direction in ["right", "left"]:
                r = rotate_stations(deepcopy(grouped_rotation_components),
                                    direction, G, Q)
                if r is not None:
                    results.append([r[i] for i in routes_indices])
        return results

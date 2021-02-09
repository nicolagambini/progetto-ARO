from itertools import permutations
from .models import Route, Solution


def get_load_window(route, i, Q, t="normal"):
    cr_i = route.cumulative_requests[i][t]
    crr_min, crr_max = route.get_cumulative_requests_interval(t, limit=i)
    return {
        "start": cr_i - crr_min,
        "end": cr_i + Q - crr_max
    }


def forward_load_window(route, i, Q):
    return get_load_window(route, i, Q, t="normal")


def backward_load_window(route, i, Q):
    return get_load_window(route, i, Q, t="reverse")


def routes_load_windows_overlap(p, r, Q, p_node_idx, r_node_idx):
    F = forward_load_window(p, p_node_idx, Q)
    B = backward_load_window(r, r_node_idx, Q)
    # merge between routes is feasible if F and B overlap in some way
    return (F["start"] <= B["end"]) and (F["end"] >= B["start"])


def is_merge_feasible(p, r, Q):
    return routes_load_windows_overlap(p, r, Q,
                                       p_node_idx=len(p.nodes)-2,
                                       r_node_idx=1)


def merge_routes(G, p, r, Q):
    m = [n.index for n in p.nodes[:-1]] + [m.index for m in r.nodes[1:]]
    return Route(G, m, Q)


def savings_and_losses(G, Q, alpha=.7335):
    assert 0 <= alpha <= 1
    # init routes
    stations = list(G.nodes)[1:]
    routes = {idx: Route(G, [0, s, 0], Q) for idx, s in enumerate(stations)}
    # iterate construction (merge routes)
    while True:
        rankings = {}
        # generate candidate merges
        for p_idx, r_idx in permutations(routes.keys(), 2):
            p, r = routes[p_idx], routes[r_idx]
            if not is_merge_feasible(p, r, Q):
                continue
            merge = merge_routes(G, p, r, Q)
            # compute scores
            saving = G.edges[0, r.nodes[1].index]["weight"] +\
                     G.edges[p.nodes[-2].index, 0]["weight"] -\
                     G.edges[r.nodes[1].index, p.nodes[-2].index]["weight"]
            loss = -(p.feasibility_amount + r.feasibility_amount -
                     2 * merge.feasibility_amount)
            E = alpha*saving + (1-alpha)*loss
            # add merge (with score) in the
            rankings[(p_idx, r_idx)] = E
        if not any(rankings):
            # exit if no more merges can be done
            break
        # add the best merges to the routes, removing the ones who originated it
        idx_bp, idx_br = max(rankings, key=rankings.get)
        routes[idx_bp] = merge_routes(
            G,
            Route(G, routes[idx_bp].as_list_of_nodes_indices(), Q),
            Route(G, routes[idx_br].as_list_of_nodes_indices(), Q),
            Q
        )
        del routes[idx_br]

    return Solution(G, list(routes.values()), Q)



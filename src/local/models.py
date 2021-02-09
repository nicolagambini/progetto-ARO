import os
import numpy as np
import networkx as nx


class Problem:

    def __init__(self, filepath, is_vnd=False):
        # set problem's name and variant (VNS or VND)
        self.name = os.path.splitext(os.path.basename(filepath))[0]
        self.variant = "vnd" if is_vnd else "vns"
        # import and preprocess problem models (from file)
        self._import_data_from_file(filepath)
        self._process_data()
        # build problem graph
        self._build_problem_graph()

    def _import_data_from_file(self, filepath):
        with open(filepath) as f:
            # 1. retrieve number of stations
            self.stations_count = int(f.readline())
            # 2. retrieve station demands
            raw_demands = f.readline().strip().split("\t")
            self.demands = {i: int(d) for i, d in enumerate(raw_demands)}
            # 3. retrieve vehicles capacity
            self.vehicles_capacity = int(f.readline())
            # 4. retrieve distance matrix
            matrix_dimensions = tuple([self.stations_count] * 2)
            self.distance_matrix = np.empty(matrix_dimensions)
            for i in range(self.stations_count):
                line = f.readline().strip().split("\t")
                for j, d in enumerate(line):
                    self.distance_matrix[i, j] = float(d)

    def _process_data(self):
        q = self.vehicles_capacity
        n = self.stations_count
        # precompute station thetas
        self.thetas = {i: max(0, min(q+d, q)) for i, d in self.demands.items()}
        # precompute thetas partial min/max (opt. to compute Us and Ds later)
        self.thetas_hashmap = {}
        for i in range(n):
            self.thetas_hashmap[i] = {
                "before_idx": {
                    "min": min(self.thetas[j] for j in range(i + 1)),
                    "max": max(self.thetas[j] for j in range(i + 1))
                },
                "after_idx": {
                    "min": min(self.thetas[j] for j in range(i, n)),
                    "max": max(self.thetas[j] for j in range(i, n))
                }
            }

    def _build_problem_graph(self):
        self.G = nx.DiGraph()
        # add stations (node) to the graph with their demand as an attribute
        nodes_info = [(node_id, {"demand": demand})
                      for node_id, demand in self.demands.items()]
        self.G.add_nodes_from(nodes_info)
        # add edges, using the euclidean distance between stations as weight
        edges_info = [(u, v, self.distance_matrix[u, v])
                      for u in range(self.stations_count)
                      for v in range(self.stations_count)
                      if u != v]

        self.G.add_weighted_edges_from(edges_info)

    def __str__(self):
        return self.name


class Node:

    def __init__(self, G, node_idx):
        self.index = node_idx
        self.demand = G.nodes[node_idx]["demand"]


class Route:

    def __init__(self, G, nodes, Q):
        self.nodes = [Node(G, n) for n in nodes]
        self.cumulative_requests = [self.get_cumulative_request(i)
                                    for i in range(len(nodes))]
        self.feasibility_amount = self._get_feasibility_amount(Q)

    def get_cumulative_request(self, i):
        return {
            "normal": sum([node.demand
                           for j, node in enumerate(self.nodes) if j <= i]),
            "reverse": -sum([node.demand
                             for j, node in enumerate(self.nodes) if j >= i])
        }

    def get_cumulative_requests_interval(self, t="normal", limit=None):
        if limit is None:
            limit = len(self.nodes)-1
        # define target cumulative requests
        partial_cumulative_requests = None
        if t == "normal":
            partial_cumulative_requests = self.cumulative_requests[:limit+1]
        else:
            partial_cumulative_requests = self.cumulative_requests[limit:]
        # get cumulative requests values and determine min and max
        limited_cr = [cr[t] for cr in partial_cumulative_requests]
        return min(limited_cr), max(limited_cr)

    def _get_feasibility_amount(self, Q):
        cri_min, cri_max = self.get_cumulative_requests_interval()
        return Q - cri_max + cri_min

    def as_list_of_nodes_indices(self):
        return [n.index for n in self.nodes]

    def as_hash(self):
        return self.__hash__()

    def __str__(self):
        return str(self.as_list_of_nodes_indices())


class Solution:

    def __init__(self, G, routes, Q):
        self.routes = routes
        self.fobj_val = self._evaluate(G, Q)

    def _evaluate(self, G, Q):
        visited_nodes = set()
        total_cost = 0
        for route in self.routes:
            route_stations_indices = route.as_list_of_nodes_indices()[1:-1]
            # return None if route has repetitions
            if len(route_stations_indices) > len(set(route_stations_indices)):
                return float("inf")  ## None
            for u, v in zip(route.nodes, route.nodes[1:]):
                # return None if any node has already been visited
                if u.index != 0 and u.index in visited_nodes:
                    return float("inf")  ## None
                visited_nodes.add(u.index)
                total_cost += G.edges[u.index, v.index]["weight"]
        # return none if not all nodes have been visited
        if len(set(G.nodes).difference(visited_nodes)) > 0:
            return float("inf")  ## None
        return total_cost

    def _get_routes_as_str(self):
        return os.linesep.join(["\t{}".format(str(r.as_list_of_nodes_indices()))
                                for r in self.routes])

    def as_hash(self):
        return hash(self._get_routes_as_str())

    def get_routes_as_csv(self):
        return ';'.join([str(r.as_list_of_nodes_indices())
                         for r in self.routes])

    def __str__(self):
        lines = [
            "Routes ({}):{}{}".format(len(self.routes), os.linesep, self._get_routes_as_str()),
            "F.obj. value: {}".format("{:.2f}".format(self.fobj_val) if self.is_feasible else "-")
        ]
        return os.linesep.join(lines)

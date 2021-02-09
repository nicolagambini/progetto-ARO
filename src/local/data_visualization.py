from pylab import *
import networkx as nx
from copy import deepcopy


def get_colormap(sampling_size, mpl_colormap):

    # populate local colormap
    hex_colors = []
    # use matplotlib given colormap (hex version)
    cmap = cm.get_cmap(mpl_colormap, min(sampling_size, 256))
    for i in range(cmap.N):
        rgba = cmap(i)
        hex_colors.append(matplotlib.colors.rgb2hex(rgba))
    return hex_colors


class ProblemPlotter:

    def __init__(self, problem):
        self.problem = problem
        self.pos = nx.spring_layout(problem.G)

    def plot(self, ax, solution=None, edge_width=1.0):

        H = self.problem.G

        # delivery stations are blue, pickup stations are red; depot is green
        nodes_demands = nx.get_node_attributes(self.problem.G, "demand")
        abs_max_demand = max([abs(demand) for demand in nodes_demands.values()])
        hex_colors = get_colormap(abs_max_demand*2+1, "coolwarm")
        node_colors = ["#81c784" if i == 0 else
                        hex_colors[demand+abs_max_demand]
                        for i, demand in nodes_demands.items()]

        # draw solution paths (if provided)
        if solution is not None:
            hex_colors = get_colormap(len(solution.routes), "Set2")
            arrows = {}  # dictionary to be used to build the plot legend
            for v_idx, route in enumerate(solution.routes):
                route_nodes = route.as_list_of_nodes_indices()
                if len(route_nodes) < 2:
                    continue
                # determine current path color
                path_color = hex_colors[v_idx % len(hex_colors)]
                # determine edges involved in current path (2-by-2 couples)
                edges_subset = list(zip(route_nodes, route_nodes[1:]))
                # draw current path
                ap = nx.draw_networkx_edges(H, self.pos, edgelist=edges_subset,
                                            edge_color=path_color,
                                            width=edge_width, style="dotted",
                                            ax=ax)
                arrows[v_idx] = ap[0]
            ax.legend(arrows.values(), ["Vehicle {}".format(v_idx)
                                        for v_idx in arrows.keys()])
        else:
            edges_colormap = cm.get_cmap("viridis_r")
            weights = [data["weight"] for e, data in dict(H.edges).items()]
            nx.draw_networkx_edges(H, self.pos, arrows=True, edge_color=weights,
                                   width=edge_width, edge_cmap=edges_colormap,
                                   connectionstyle='arc3,rad=0.03')

        # draw problem nodes (with labels and demands)
        nx.draw_networkx_nodes(H, self.pos, node_color=node_colors, label="x", ax=ax)
        nx.draw_networkx_labels(H, self.pos, font_color="w", font_weight="semibold", ax=ax)

        # ax settings
        ax.set_title(self.problem.name)
        ax.set_facecolor("#ede7f6")  # used to contrast edges colormap
        ax.axes.get_xaxis().set_visible(False)
        ax.axes.get_yaxis().set_visible(False)

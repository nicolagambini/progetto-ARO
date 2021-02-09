from ..constructive_methods import *


def check_property_1(p, r, p_pos):
    # if p==q this check isn't necessary: skip it
    if p.as_hash() == r.as_hash():
        return True
    # q_i > dest_route.delta (station i not in dest_route)
    if abs(p.nodes[p_pos].demand) > r.feasibility_amount:
        return False
    return True


def check_property_2a_2b(p, r, p_pos):
    # if p!=q this check isn't necessary: skip it
    if p.as_hash() != r.as_hash():
        return True
    # q_i > dest_route.delta (station i in dest_route)
    if abs(p.nodes[p_pos].demand) > p.feasibility_amount:
        return False
    return True


def check_property_2c(p, r, p_pos, r_pos):
    # if p!=q this check isn't necessary: skip it
    if p.as_hash() != r.as_hash():
        return True
    i_demand, j_demand = p.nodes[p_pos].demand, p.nodes[r_pos].demand
    if abs(i_demand - j_demand) > p.feasibility_amount:
        return False
    return True


def check_property_2d(p, r, p_pos, r_pos):
    # if p==q this check isn't necessary: skip it
    if p.as_hash() == r.as_hash():
        return True
    i_demand, j_demand = p.nodes[p_pos].demand, r.nodes[r_pos].demand
    feasibility_amounts = [p.feasibility_amount, r.feasibility_amount]
    if abs(i_demand - j_demand) > min(feasibility_amounts):
        return False
    return True


def check_property_3(Q, p, r):
    windows_overlap = routes_load_windows_overlap(p, r, Q, len(p.nodes)-2, 1)
    return windows_overlap


def check_property_4b(Q, p, p_pos):
    windows_overlap = routes_load_windows_overlap(p, p, Q, p_pos-1, p_pos+1)
    return windows_overlap


def check_property_4c(Q, p, r, p_pos, r_pos):
    if len(p.nodes) == 3:
        # condition 4c.1
        i_demand = p.nodes[1].demand
        Bi = (0, Q-i_demand) if i_demand >= 0 else (-i_demand, Q)
        Fp = forward_load_window(r, r_pos, Q)
        condition_1 = (Fp["start"] <= Bi[1]) and (Fp["end"] >= Bi[0])
        if not condition_1:
            return False
        # condition 4c.2
        Fi = (max(Fp["start"], Bi[0]) + p.get_cumulative_request(p_pos)["normal"],
              min(Fp["end"], Bi[1]) + p.get_cumulative_request(p_pos)["normal"])
        Bp = backward_load_window(r, r_pos+1, Q)
        condition_2 = (Bp["start"] <= Fi[1]) and (Bp["end"] >= Fi[0])
        if not condition_2:
            return False
    return True


def check_property_4d(Q, p, r, p_pos, r_pos):
    ##I = [0, p.nodes[p_pos].index, 0]
    ##J = [0, r.nodes[r_pos].index, 0]
    # condition 4d.1
    j_demand = r.nodes[r_pos].demand
    Fp = forward_load_window(p, p_pos-1, Q)
    Bj = (0, Q-j_demand) if j_demand >= 0 else (-j_demand, Q)
    condition_1 = (Fp["start"] <= Bj[1]) and (Fp["end"] >= Bj[0])
    if not condition_1:
        return False
    # condition 4d.2
    Fj = (max(Fp["start"], Bj[0]) + j_demand, min(Fp["end"], Bj[1]) + j_demand)
    Bp = backward_load_window(p, p_pos+1, Q)
    condition_2 = (Fj[0] <= Bp["start"]) and (Fj[1] >= Bp["end"])
    if not condition_2:
        return False
    # condition 4d.3
    i_demand = p.nodes[p_pos].demand
    Fr = forward_load_window(r, r_pos-1, Q)
    Bi = (0, Q-i_demand) if i_demand >= 0 else (-i_demand, Q)
    condition_3 = (Fr["start"] <= Bi[1]) and (Fr["end"] >= Bi[0])
    if not condition_3:
        return False
    # condition 4d.4
    Fi = (max(Fr["start"], Bi[0]) + i_demand, min(Fr["end"], Bi[1]) + i_demand)
    Br = backward_load_window(r, r_pos+1, Q)
    condition_4 = (Fi[0] <= Br["start"]) and (Fi[1] >= Br["end"])
    if not condition_4:
        return False
    return True


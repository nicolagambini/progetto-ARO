import sys
from enum import Enum
from copy import deepcopy
from time import time
import random


class StoppingCondition(Enum):
    LOCAL_OPTIMUM_FOUND = 0x0
    MAX_IT_REACHED = 0x1
    MAX_TIME_REACHED = 0x2
    MAX_CONSECUTIVE_SOLUTIONS = 0x3

    def __int__(self):
        return self.value


def local_search(initial_solution, neighborhood_generator_class, tolerance, G, Q):
    best_solution = deepcopy(initial_solution)
    while True:
        generator = neighborhood_generator_class(best_solution)
        neighbors = generator.generate_neighbors(G, Q)
        if len(neighbors) == 0:
            break
        best_neighbor = min(neighbors, key=lambda x: x.fobj_val)
        # in no better neighbor was found or max tolerance was reached, return
        if best_neighbor.fobj_val >= best_solution.fobj_val or \
           abs(best_neighbor.fobj_val - best_solution.fobj_val) < tolerance:
            break
        best_solution = best_neighbor
    has_improved = (best_solution.fobj_val < initial_solution.fobj_val)
    return has_improved, best_solution


def vns(problem, initial_solution, neighborhood_generators, descend=False,
        max_it=5000, max_consecutive_solutions=20, tolerance=1e-50,
        max_time=10):
    best_solution = deepcopy(initial_solution)
    debug_mode = sys.gettrace() is not None
    t0 = time()
    k, it, consecutive_solutions_count = 0, 0, 0
    run_details = [{
        "it": 0,
        "instant": 0,
        "local_optimum_value": initial_solution.fobj_val
    }]
    while k < len(neighborhood_generators):
        # define neighborhood
        generator_class = neighborhood_generators[k]
        generator = generator_class(best_solution)
        ##print(generator.__class__)
        neighborhood = generator.generate_neighbors(G=problem.G,
                                                    Q=problem.vehicles_capacity)
        is_solution_consecutive = False
        if not any(neighborhood):
            k += 1
            if k == len(neighborhood_generators):
                if descend:
                    return it, best_solution, \
                           StoppingCondition.LOCAL_OPTIMUM_FOUND, run_details
                else:
                    k = 0
        else:
            # perform local search on candidate solution (current best solution
            # if descend; else, a random element from the current neighborhood)
            if descend:
                ls_seed = best_solution
            else:
                ls_seed = random.choice(neighborhood)
            has_improved, ls_solution = local_search(ls_seed,
                                                     generator_class,
                                                     tolerance,
                                                     G=problem.G,
                                                     Q=problem.vehicles_capacity)
            if ls_solution.fobj_val <= best_solution.fobj_val:
                if ls_solution.as_hash() == best_solution.as_hash():
                    is_solution_consecutive = True
                best_solution = deepcopy(ls_solution)
                k = 0
            else:
                k += 1
                if k == len(neighborhood_generators):
                    if descend:
                        return it, best_solution, \
                               StoppingCondition.LOCAL_OPTIMUM_FOUND, \
                               run_details
                    else:
                        k = 0
        # fix time instant (current iteration) and increment iteration counter
        t = time()-t0
        it += 1
        # save current iteration details
        run_details.append({
            "it": it,
            "instant": t,
            "local_optimum_value": best_solution.fobj_val
        })
        # increment consecutive solutions count if current solution is the same
        # as the previous one; otherwise, reset the counter
        if is_solution_consecutive:
            consecutive_solutions_count += 1
        else:
            consecutive_solutions_count = 0
        # time limit check
        if not debug_mode and t > max_time:
            return it, best_solution,\
                   StoppingCondition.MAX_TIME_REACHED, run_details
        # iterations limit check
        if it >= max_it:
            return it, best_solution, \
                   StoppingCondition.MAX_IT_REACHED, run_details
        # consecutive equal solutions count
        if consecutive_solutions_count >= max_consecutive_solutions:
            return it, best_solution, \
                   StoppingCondition.MAX_CONSECUTIVE_SOLUTIONS, run_details

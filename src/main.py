import os
import argparse
import matplotlib.pyplot as plt
from time import time
from datetime import datetime
import pandas as pd
import pickle

from local.models import Problem
from local.data_visualization import ProblemPlotter
from local.constructive_methods import savings_and_losses
from local.neighborhoods import neighborhood_generators
from local.search_methods import vns


RUNS_INFO_FILENAME = "runs_info.csv"
RUNS_INFO_HEADER = [
    "datetime_str",
    "initial_solution_value",
    "initial_solution_routes",
    "local_optimum_value",
    "local_optimum_routes",
    "exit_condition",
    "exec_time"
]
SINGLE_RUN_INFO_FILENAME = "info.csv"
SINGLE_RUN_INFO_HEADER = [
    "it",
    "instant",
    "local_optimum_value"
]


def plot_problem(pp, solution=None, edge_width=1.0, savefig_path=None):
    fig, ax = plt.subplots(figsize=(8, 6))
    # plot problem (and solution, if given) in ax
    pp.plot(ax, solution, edge_width)
    if savefig_path is None:
        plt.show()
    else:
        plt.savefig(savefig_path)


if __name__ == "__main__":

    # parse execution arguments
    parser = argparse.ArgumentParser(description="Script that executes the " +
        "VNS algorithm (or its VND variant, if specified) on a given " +
        "benchmark instance")
    parser.add_argument("dataset_file", help="path of the target benchmark " +
         "instance")
    parser.add_argument("time_limit", type=int, help="maximum execution time " +
        "allowed (in seconds)")
    parser.add_argument('-d', dest='descend', action='store_true', help="if " +
        "specified, it causes the execution of the VND variant of the method; " +
        "if not, the VNS variante will be run instead")
    parser.add_argument('-p', dest='plot_problem', action='store_true', help=\
        "if specified, the given problem complete graph will be plotted and " +
        "saved to file (not recommended for medium or large instances)")
    parser.add_argument('-a', dest='annotate_results', action='store_true',
        help="if specified, the details about each iteration will be printed " +
             "out to a .csv file (located in /results/<instance_filename>/)")
    parser.add_argument('--isp', dest='initial_solution_path', help="filepath " +
        "of the pre-computed initial solution .sol file (can be used to " +
        "reduce the total excection time)")
    args = parser.parse_args()

    # retrieve given problem's model
    p = Problem(args.dataset_file, args.descend)

    # fix current datetime
    initial_dt_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")

    # COMPUTE INITIAL SOLUTION ---
    # try to retrieve the initial solution from file, if corresponding file
    # exists; otherwise, compute it and save to file for further usage
    initial_solutions_file_exists = os.path.isfile(args.initial_solution_path) \
        if (args.initial_solution_path is not None) else None
    if not initial_solutions_file_exists:
        # create initial results folder (if not present)
        initial_solutions_folder = os.path.sep.join(["..", "initial_solutions"])
        if not os.path.isdir(initial_solutions_folder):
            os.makedirs(initial_solutions_folder)
        # generate initial solution using savings&losses
        initial_solution = savings_and_losses(p.G, p.vehicles_capacity)
        # save the solution to file
        initial_solution_filepath = os.path.sep.join([initial_solutions_folder,
                                                      p.name + ".sol"])
        with open(initial_solution_filepath, "wb") as f:
            pickle.dump(initial_solution, f)
    else:
        # read the solution from file
        with open(args.initial_solution_path, "rb") as f:
            initial_solution = pickle.load(f)
    # ---

    # get optimal solution
    t0 = time()
    it, best_solution, stop_criteria, run_details = \
        vns(p, initial_solution, neighborhood_generators,
            max_time=args.time_limit, descend=args.descend)
    exec_time = time()-t0

    # results annotation
    p_plotter = ProblemPlotter(p)
    if not args.annotate_results:

        # print run info
        print("Number of iterations: {}".format(it))
        print("Best solution found ---{}{}".format(os.linesep, best_solution))
        print("---")
        print("Stop criteria: {}".format(stop_criteria))
        print("Execution time: {:.2f} sec".format(exec_time))
        print(run_details)

        # show solution plot
        plot_problem(p_plotter, best_solution)

    else:

        # SAVE RUN INFO ========================================================

        results_folder = os.path.sep.join(["..", "results", p.name, p.variant])
        # create result folder (if not present)
        if not os.path.isdir(results_folder):
            os.makedirs(results_folder)

        # save run info
        runs_info_file = os.path.sep.join([results_folder, RUNS_INFO_FILENAME])
        # try to retrieve past results CSV file; if not present, create it
        if os.path.isfile(runs_info_file):
            ri_df = pd.read_csv(runs_info_file, index_col="datetime_str")
        else:
            ri_df = pd.DataFrame(columns=RUNS_INFO_HEADER)
            ri_df.set_index("datetime_str", inplace=True)
        # append current run results to the pd.Dataframe
        ri_s = pd.Series({
            "initial_solution_value": initial_solution.fobj_val,
            "initial_solution_routes": initial_solution.get_routes_as_csv(),
            "local_optimum_value": best_solution.fobj_val,
            "local_optimum_routes": best_solution.get_routes_as_csv(),
            "exit_condition": int(stop_criteria),
            "exec_time": exec_time
        })
        ri_s.name = initial_dt_str
        ri_df = ri_df.append(ri_s)
        # save updated dataframe to a CSV file
        ri_df.to_csv(runs_info_file)

        # plot problem graph (without solution) iff it hasn't been already did
        problem_fig_path = os.path.sep.join([results_folder, "problem.png"])
        if args.plot_problem and not os.path.isfile(problem_fig_path):
            plot_problem(p_plotter, savefig_path=problem_fig_path)

        # SAVE RUN DETAILS =====================================================

        runs_results_folder = os.path.sep.join([results_folder, "runs",
                                                initial_dt_str])
        # create single runs results folder (if not present)
        if not os.path.isdir(runs_results_folder):
            os.makedirs(runs_results_folder)

        # create CSV file containing the details of the current run
        sri_df = pd.DataFrame(run_details)
        sri_df.set_index("it", inplace=True)
        single_run_info_file = os.path.sep.join([runs_results_folder,
                                                 SINGLE_RUN_INFO_FILENAME])
        sri_df.to_csv(single_run_info_file)

        # plot local optimum's solution graph
        solution_fig_path = os.path.sep.join([runs_results_folder,
                                              "solution.png"])
        plot_problem(p_plotter, solution=best_solution,
                     savefig_path=solution_fig_path)

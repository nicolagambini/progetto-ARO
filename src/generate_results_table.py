import os
import glob
import argparse
import re
import pandas as pd


if __name__ == "__main__":

    # parse execution arguments
    parser = argparse.ArgumentParser(description="Script that collects the " +
        "results obtained from the runs performed on the benchmark instances " +
        "(located in /results/) and it combines their information into a " +
        "single .csv file")
    parser.add_argument("target", choices=["vns", "vnd"], help="variant of " +
        "the method whose results will be considered")
    args = parser.parse_args()

    # iterate instances results
    folders_info = []
    folders_query_str = os.path.sep.join(["..", "results", "*", args.target,
                                          "runs_info.csv"])
    for folder_path in list(glob.iglob(folders_query_str, recursive=True)):
        # split instance folder name in [index, city, vehicles_capacity]
        folder_name = os.path.normpath(folder_path).split(os.path.sep)[2]
        index, city, vehicles_capacity = re.split(r'(\d+)', folder_name)[1:-1]
        # retrieve instance results DataFrame
        results_df = pd.read_csv(folder_path)
        # determine best local optimum
        blo_idx = results_df["local_optimum_value"].idxmin()
        blo_val = results_df.loc[blo_idx].local_optimum_value
        blo_dts = results_df.loc[blo_idx].datetime_str
        # compute average execution time
        avg_exec_time = results_df["exec_time"].mean()
        # compute average f.obj. %gap between the solutions and the optimal one
        avg_solution_value = results_df["local_optimum_value"].mean()
        avg_percentage_gap = 100 * (avg_solution_value - blo_val) / blo_val
        # summarize the computed info
        folders_info.append({
            "original_idx": int(index),
            "city": city,
            "vehicles_capacity": vehicles_capacity,
            "local_optimum_datetime_str": blo_dts,
            "local_optimum_value": blo_val,
            "avg_percentage_gap": avg_percentage_gap,
            "avg_execution_time": avg_exec_time
        })

    # sort results table by instance index ASC and vehicles capacity DESC
    results_table = pd.DataFrame(folders_info)
    results_table.sort_values("original_idx", ascending=True, inplace=True)
    results_table.set_index("original_idx", inplace=True)

    # save results table to file
    save_path = os.path.sep.join(["..", "results",
                                  "{}_global_results.csv".format(args.target)])
    results_table.to_csv(save_path)

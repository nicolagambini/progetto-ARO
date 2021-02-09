import os
import glob
import shutil
from tqdm import tqdm
import argparse

from local.models import Problem


TIME_LIMIT_PER_TYPE = {
    "small": 15,
    "medium": 600,
    "large": 1800
}
NUMBER_OF_RUNS = 10
OVERWRITE_RESULTS = False
SKIP_EXISTING = True


class FileDescriptor:

    def __init__(self, fp):
        self.full_path = fp
        # get problem name from filepath
        file_name = os.path.basename(fp)
        self.problem_name = os.path.splitext(file_name)[0]
        # get problem type (small, medium or large)
        self.type = fp.split(os.sep)[2]

    def get_results_folder(self):
        return os.path.sep.join(["..", "results", self.problem_name])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Script that automates the " +
        "execution of multiple runs on each available benchmark instance. " +
        "Please refer to the internal variables if you need to fine tune " +
        "the execution of this process (note: these variables are declared " +
        "at the beginning of this script, written in uppercase)")
    args = parser.parse_args()

    # iterate datasets
    target_files_wildcard = os.path.sep.join(["..", "data", "*", "*.txt"])
    filepaths = list(glob.iglob(target_files_wildcard, recursive=True))
    for filepath in tqdm(sorted(filepaths, reverse=True)):

        # build dataset object
        fd = FileDescriptor(filepath)

        # if problem directory already exists...
        results_folder = fd.get_results_folder()
        if os.path.isdir(results_folder):
            # A) if overwrite mode, delete the entire folder
            if OVERWRITE_RESULTS:
                shutil.rmtree(results_folder)
            # B) if not overwrite mode and skip existing folders, skip
            elif SKIP_EXISTING:
                continue

        # determine runs tuning
        # - time limit
        time_limit = TIME_LIMIT_PER_TYPE[fd.type]
        # - determine if problem graph needs to be plotted
        p = Problem(fd.full_path)
        plot_problem_graph = (p.stations_count <= 20)
        # - precomputed initial solution path
        initial_solution_path = os.path.sep.join(["..", "results",
                                                  "{}.sol".format(p.name)])

        # execute both VNS and VND variant
        for variant in tqdm(["vns", "vnd"]):
            runs_count = NUMBER_OF_RUNS if variant == "vns" else 1
            for run_count in tqdm(range(runs_count)):
                arguments = [filepath, str(time_limit),
                             "--isp={}".format(initial_solution_path),
                             "-a"]
                if variant == "vnd":
                    arguments.append("-d")
                if plot_problem_graph:
                    arguments.append("-p")
                os.system("python main.py " + " ".join(arguments))

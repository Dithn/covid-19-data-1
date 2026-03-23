import argparse

CHOICES = ["etl", "grapher-file", "explorer-file"]


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Execute COVID-19 Hospitalisation data collection pipeline.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "step",
        choices=CHOICES,
        default="etl",
        help=(
            "Choose a step: 1) `etl` to get all data and DS ready file, 2) `grapher-file` to generate"
            " a grapher-friendly file, 3) `explorer-file` to generate a explorer-friendly file."
        ),
    )
    parser.add_argument(
        "-p",
        "--monothread",
        action="store_true",
        help="Execution done in monothread. Otherwise, it is parallelized.",
    )
    parser.add_argument(
        "-j",
        "--njobs",
        default=-2,
        help=(
            "Number of jobs for parallel processing. Check Parallel class in joblib library for more info  (only in "
            "mode get-data)."
        ),
    )
    args = parser.parse_args()
    return args

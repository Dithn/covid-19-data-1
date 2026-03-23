import argparse

CHOICES = ["etl", "grapher-file"]


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Execute COVID-19 US States data collection pipeline.",
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
    args = parser.parse_args()
    return args

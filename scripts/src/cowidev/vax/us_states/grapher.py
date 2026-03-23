from datetime import datetime

from cowidev.grapher.files import Exploriser, Grapheriser


def run_grapheriser(input_path: str, output_path: str):
    Grapheriser(
        fillna_0=False,
        date_ref=datetime(2021, 1, 1),
    ).run(input_path, output_path)


def run_explorerizer(input_path: str, output_path: str):
    raise NotImplementedError("Not implemented")

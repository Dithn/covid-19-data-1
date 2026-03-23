import os

from cowidev import PATHS
from .etl import run_etl
from .grapher import run_explorerizer
from ._parser import _parse_args


FILE_DS = PATHS.DATA_XM_MAIN_FILE
FILE_EXPLORER = os.path.join(PATHS.DATA_INTERNAL_DIR, "megafile--excess-mortality.json")


def run_step(step: str):
    if step == "etl":
        run_etl()
    elif step == "explorer-file":
        run_explorerizer(FILE_DS, FILE_EXPLORER)


if __name__ == "__main__":
    args = _parse_args()
    run_step(args.step)

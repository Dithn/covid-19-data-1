import os

from cowidev import PATHS
from cowidev.vax.us_states._parser import _parse_args
from cowidev.vax.us_states.etl import run_etl
from cowidev.vax.us_states.grapher import run_grapheriser

FILE_DS = PATHS.DATA_VAX_US_FILE
FILE_GRAPHER = os.path.join(PATHS.INTERNAL_GRAPHER_DIR, "COVID-19 - United States vaccinations.csv")


def run_step(step: str):
    if step == "etl":
        run_etl(FILE_DS)
    elif step == "grapher-file":
        run_grapheriser(FILE_DS, FILE_GRAPHER)
    # elif step == "explorer-file":
    #     run_explorerizer(FILE_DS, FILE_EXPLORER)


if __name__ == "__main__":
    args = _parse_args()
    run_step(args.step)

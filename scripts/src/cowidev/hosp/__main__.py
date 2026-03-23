from cowidev.hosp._parser import _parse_args
from cowidev.hosp.etl import run_etl
from cowidev.hosp.grapher import run_grapheriser


def run_step(args):
    if args.step == "etl":
        run_etl(not args.monothread, args.njobs)
    elif args.step == "grapher-file":
        run_grapheriser()


if __name__ == "__main__":
    args = _parse_args()
    run_step(args)

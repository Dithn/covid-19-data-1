from cowidev import PATHS
from cowidev.utils.s3 import obj_to_s3
from cowidev.vax.batch.latvia import Latvia


countries = [Latvia()]


def main(logger):
    for country in countries:
        logger.info(f"VAX - ICE - {country.location}")
        df = country.read()
        obj_to_s3(df, f"{PATHS.S3_VAX_ICE_DIR}/{country.location}.csv")


if __name__ == "__main__":
    main()

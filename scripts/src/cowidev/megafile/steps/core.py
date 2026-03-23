import os

from cowidev import PATHS
from cowidev.megafile.steps.cgrt import get_cgrt
from cowidev.megafile.steps.hosp import get_hosp
from cowidev.megafile.steps.cases_deaths import get_casedeath
from cowidev.megafile.steps.reprod import get_reprod
from cowidev.megafile.steps.test import get_testing
from cowidev.megafile.steps.variants import get_variants
from cowidev.megafile.steps.vax import get_vax


INPUT_DIR = PATHS.INTERNAL_INPUT_DIR
GRAPHER_DIR = PATHS.INTERNAL_GRAPHER_DIR
DATA_DIR = PATHS.DATA_DIR


def get_base_dataset(logger):
    """Get owid datasets from: who, reproduction rate, hospitalizations, testing, vaccinations, CGRT."""
    path = PATHS.DATA_CASES_DEATHS_DIR

    logger.info("Fetching Case/Death dataset…")
    cases_deaths = get_casedeath(dataset_dir=path)

    logger.info("Fetching reproduction rate…")
    try:
        reprod = get_reprod(
            file_url="https://github.com/crondonm/TrackingR/raw/main/Estimates-Database/database_7.csv",
            country_mapping=os.path.join(INPUT_DIR, "reproduction", "reprod_country_standardized.csv"),
        )
    except:
        reprod = get_reprod(
            file_url="https://github.com/crondonm/TrackingR/raw/main/Estimates-Database/database_7.csv",
            country_mapping=os.path.join(INPUT_DIR, "reproduction", "reprod_country_standardized.csv"),
        )

    logger.info("Fetching hospital dataset…")
    hosp = get_hosp(data_file=os.path.join(GRAPHER_DIR, "COVID-2019 - Hospital & ICU.csv"))

    logger.info("Fetching testing dataset…")
    testing = get_testing()

    logger.info("Fetching vaccination dataset…")
    vax = get_vax(data_file=os.path.join(DATA_DIR, "vaccinations", "vaccinations.csv"))
    # vax = vax[-vax.location.isin(["England", "Northern Ireland", "Scotland", "Wales"])]

    logger.info("Fetching OxCGRT dataset…")
    cgrt = get_cgrt(
        bsg_latest=os.path.join(INPUT_DIR, "bsg", "latest.csv"),
        bsg_diff_latest=os.path.join(INPUT_DIR, "bsg", "latest-differentiated.csv"),
        country_mapping=os.path.join(INPUT_DIR, "bsg", "bsg_country_standardised.csv"),
    )

    logger.info("Fetching variants dataset…")
    variants = get_variants(
        variants_file="s3://covid-19/internal/variants/covid-variants.csv",
        cases_file=os.path.join(path, "full_data.csv"),
    )

    # Big merge
    return (
        cases_deaths.merge(reprod, on=["date", "location"], how="outer")
        .merge(hosp, on=["date", "location"], how="outer")
        .merge(testing, on=["date", "location"], how="outer")
        .merge(vax, on=["date", "location"], how="outer")
        .merge(cgrt, on=["date", "location"], how="left")
        .merge(variants, on=["date", "location"], how="left")
        .sort_values(["location", "date"])
    )

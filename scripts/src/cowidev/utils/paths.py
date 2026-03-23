import os

from cowidev.utils.exceptions import EnvironmentError

# S3 ####################################
S3_DIR = "s3://covid-19"
S3_INTERNAL_DIR = f"{S3_DIR}/internal"
S3_INTERNAL_VAX_DIR = f"{S3_INTERNAL_DIR}/vax"
S3_VAX_ICE_DIR = f"{S3_INTERNAL_VAX_DIR}/ice"


# PROJECT DIR ###########################
def _get_project_dir_from_env(err: bool = False):
    project_dir = os.environ.get("OWID_COVID_PROJECT_DIR", "/home/lucas/repos/covid-19-data")
    if project_dir is None:  # err and
        raise EnvironmentError("Please set environment variable 'OWID_COVID_PROJECT_DIR'.")
    elif not os.path.isdir(project_dir):  # err and
        raise EnvironmentError(
            f"Environment variable 'OWID_COVID_PROJECT_DIR' is pointing to a non-existing folder {project_dir}."
        )
    return project_dir


PROJECT_DIR = _get_project_dir_from_env()

# Public ########
PUBLIC_DIR = os.path.join(PROJECT_DIR, "public")
DATA_DIR = os.path.join(PUBLIC_DIR, "data")
DATA_READ_FILE = os.path.join(DATA_DIR, "README.md")
DATA_CODEBOOK_FILE = os.path.join(DATA_DIR, "owid-covid-codebook.csv")
DATA_MAIN_FILE = os.path.join(DATA_DIR, "owid-covid-data.csv")

## Data excess mortality
DATA_XM_DIR = os.path.join(DATA_DIR, "excess_mortality")
DATA_XM_MAIN_FILE = os.path.join(DATA_XM_DIR, "excess_mortality.csv")
DATA_XM_ECON_FILE = os.path.join(DATA_XM_DIR, "excess_mortality_economist_estimates.csv")
DATA_XM_READ_FILE = os.path.join(DATA_XM_DIR, "README.md")
## Data hospitalizations
DATA_HOSP_DIR = os.path.join(DATA_DIR, "hospitalizations")
DATA_HOSP_MAIN_FILE = os.path.join(DATA_HOSP_DIR, "covid-hospitalizations.csv")
DATA_HOSP_META_FILE = os.path.join(DATA_HOSP_DIR, "locations.csv")
DATA_HOSP_READ_FILE = os.path.join(DATA_HOSP_DIR, "README.md")
## Data testing
DATA_TEST_DIR = os.path.join(DATA_DIR, "testing")
DATA_TEST_MAIN_FILE = os.path.join(DATA_TEST_DIR, "covid-testing-all-observations.csv")
## Data vaccinations
DATA_VAX_DIR = os.path.join(DATA_DIR, "vaccinations")
DATA_VAX_COUNTRY_DIR = os.path.join(DATA_VAX_DIR, "country_data")
DATA_VAX_MAIN_FILE = os.path.join(DATA_VAX_DIR, "vaccinations.csv")
DATA_VAX_META_FILE = os.path.join(DATA_VAX_DIR, "locations.csv")
DATA_VAX_US_FILE = os.path.join(DATA_VAX_DIR, "us_state_vaccinations.csv")
DATA_VAX_MAIN_JSON_FILE = os.path.join(DATA_VAX_DIR, "vaccinations.json")
DATA_VAX_MANUFACT_FILE = os.path.join(DATA_VAX_DIR, "vaccinations-by-manufacturer.csv")
DATA_VAX_META_MANUFACT_FILE = os.path.join(DATA_VAX_DIR, "locations-manufacturer.csv")
DATA_VAX_AGE_FILE = os.path.join(DATA_VAX_DIR, "vaccinations-by-age-group.csv")
DATA_VAX_META_AGE_FILE = os.path.join(DATA_VAX_DIR, "locations-age.csv")
DATA_VAX_READ_FILE = os.path.join(DATA_VAX_DIR, "README.md")
## Data cases/deaths
DATA_CASES_DEATHS_DIR = os.path.join(DATA_DIR, "cases_deaths")
DATA_CASES_FILE = os.path.join(DATA_CASES_DEATHS_DIR, "total_cases.csv")
DATA_DEATHS_FILE = os.path.join(DATA_CASES_DEATHS_DIR, "total_deaths.csv")
## Internal
DATA_INTERNAL_DIR = os.path.join(DATA_DIR, "internal")
DATA_INTERNAL_VAX_TABLE = os.path.join(DATA_INTERNAL_DIR, "vaccinations-source-table.html")
## Latest
DATA_LATEST_DIR = os.path.join(DATA_DIR, "latest")
## Timestamps
DATA_TIMESTAMP_DIR = os.path.join(DATA_INTERNAL_DIR, "timestamp")
DATA_TIMESTAMP_HOSP_FILE = os.path.join(DATA_TIMESTAMP_DIR, "owid-covid-data-last-updated-timestamp-hosp.txt")
DATA_TIMESTAMP_ROOT_FILE = os.path.join(DATA_TIMESTAMP_DIR, "owid-covid-data-last-updated-timestamp-root.txt")
DATA_TIMESTAMP_TEST_FILE = os.path.join(DATA_TIMESTAMP_DIR, "owid-covid-data-last-updated-timestamp-test.txt")
DATA_TIMESTAMP_VAX_FILE = os.path.join(DATA_TIMESTAMP_DIR, "owid-covid-data-last-updated-timestamp-vaccination.txt")
DATA_TIMESTAMP_XM_FILE = os.path.join(DATA_TIMESTAMP_DIR, "owid-covid-data-last-updated-timestamp-xm.txt")
DATA_TIMESTAMP_CASES_DEATHS_FILE = os.path.join(
    DATA_TIMESTAMP_DIR, "owid-covid-data-last-updated-timestamp-cases-deaths.txt"
)
DATA_TIMESTAMP_OLD_FILE = os.path.join(DATA_TIMESTAMP_DIR, "owid-covid-data-last-updated-timestamp.txt")

# Internal ########
INTERNAL_DIR = os.path.join(PROJECT_DIR, "scripts")

## Output
INTERNAL_TMP_DIR = os.path.join(INTERNAL_DIR, "tmp")
## Output
INTERNAL_OUTPUT_DIR = os.path.join(INTERNAL_DIR, "output")
### Output vax
INTERNAL_OUTPUT_VAX_DIR = os.path.join(INTERNAL_OUTPUT_DIR, "vaccinations")
INTERNAL_OUTPUT_VAX_TABLE_FILE = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "source_table.html")
INTERNAL_OUTPUT_VAX_AUTOM_FILE = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "automation_state.csv")
INTERNAL_OUTPUT_VAX_MAIN_DIR = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "main_data")
INTERNAL_OUTPUT_VAX_MANUFACT_DIR = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "by_manufacturer")
INTERNAL_OUTPUT_VAX_AGE_DIR = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "by_age_group")
INTERNAL_OUTPUT_VAX_META_DIR = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "metadata")
INTERNAL_OUTPUT_VAX_META_FILE = os.path.join(INTERNAL_OUTPUT_VAX_META_DIR, "locations.csv")
INTERNAL_OUTPUT_VAX_META_AGE_FILE = os.path.join(INTERNAL_OUTPUT_VAX_META_DIR, "locations-age.csv")
INTERNAL_OUTPUT_VAX_META_MANUFACT_FILE = os.path.join(INTERNAL_OUTPUT_VAX_META_DIR, "locations-manufacturer.csv")
INTERNAL_OUTPUT_VAX_LOG_DIR = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "log")
INTERNAL_OUTPUT_VAX_PROPOSALS_DIR = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "proposals")
INTERNAL_OUTPUT_VAX_STATUS_GET = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "status", "status-vax-get.csv")
INTERNAL_OUTPUT_VAX_STATUS_GET_TS = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "status", "status-vax-get-ts.txt")
INTERNAL_OUTPUT_VAX_STATUS_PROCESS = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "status", "status-vax-process.csv")
INTERNAL_OUTPUT_VAX_STATUS_PROCESS_TS = os.path.join(INTERNAL_OUTPUT_VAX_DIR, "status", "status-vax-process-ts.txt")
### Output test
INTERNAL_OUTPUT_TEST_DIR = os.path.join(INTERNAL_OUTPUT_DIR, "testing")
INTERNAL_OUTPUT_TEST_MAIN_DIR = os.path.join(INTERNAL_OUTPUT_TEST_DIR, "main_data")
INTERNAL_OUTPUT_TEST_STATUS_GET = os.path.join(INTERNAL_OUTPUT_TEST_DIR, "status", "status-test-get.csv")
INTERNAL_OUTPUT_TEST_STATUS_GET_TS = os.path.join(INTERNAL_OUTPUT_TEST_DIR, "status", "status-test-get-ts.txt")
### Output hospitalizations
INTERNAL_OUTPUT_HOSP_DIR = os.path.join(INTERNAL_OUTPUT_DIR, "hospitalizations")
INTERNAL_OUTPUT_HOSP_MAIN_DIR = os.path.join(INTERNAL_OUTPUT_HOSP_DIR, "main_data")
INTERNAL_OUTPUT_HOSP_META_DIR = os.path.join(INTERNAL_OUTPUT_HOSP_DIR, "metadata")
### Output variants
INTERNAL_OUTPUT_VARIANTS_FILE = "s3://covid-19/internal/variants/covid-variants.csv"
INTERNAL_OUTPUT_VARIANTS_SEQ_FILE = "s3://covid-19/internal/variants/covid-sequencing.csv"

## Input
INTERNAL_INPUT_DIR = os.path.join(INTERNAL_DIR, "input")
### Input UN
INTERNAL_INPUT_BSG_DIR = os.path.join(INTERNAL_INPUT_DIR, "bsg")
INTERNAL_INPUT_BSG_FILE = os.path.join(INTERNAL_INPUT_BSG_DIR, "latest.csv")
INTERNAL_INPUT_CDC_VAX_DIR = os.path.join(INTERNAL_INPUT_DIR, "cdc", "vaccinations")
INTERNAL_INPUT_ISO_DIR = os.path.join(INTERNAL_INPUT_DIR, "iso")
INTERNAL_INPUT_ISO_FILE = os.path.join(INTERNAL_INPUT_ISO_DIR, "iso3166_1_alpha_3_codes.csv")
INTERNAL_INPUT_ISO_FULL_FILE = os.path.join(INTERNAL_INPUT_ISO_DIR, "iso.csv")
INTERNAL_INPUT_OWID_DIR = os.path.join(INTERNAL_INPUT_DIR, "owid")
INTERNAL_INPUT_OWID_POPULATION_SUB_FILE = os.path.join(INTERNAL_INPUT_OWID_DIR, "subnational_population_2020.csv")
INTERNAL_INPUT_OWID_CONT_FILE = os.path.join(INTERNAL_INPUT_OWID_DIR, "continents.csv")
INTERNAL_INPUT_OWID_INCOME_FILE = os.path.join(INTERNAL_INPUT_OWID_DIR, "income_groups_complement.csv")
INTERNAL_INPUT_OWID_EU_FILE = os.path.join(INTERNAL_INPUT_OWID_DIR, "eu_countries.csv")
INTERNAL_INPUT_OWID_ANNOTATIONS_FILE = os.path.join(INTERNAL_DIR, "scripts", "annotations_internal.yaml")
INTERNAL_INPUT_OWID_READ_FILE = os.path.join(INTERNAL_DIR, "scripts", "README.md.template")
INTERNAL_INPUT_OWID_TESTCUT_FILE = os.path.join(INTERNAL_INPUT_OWID_DIR, "testing_cutoffs.csv")
INTERNAL_INPUT_OWID_COVID_NOTES_FILE = os.path.join(INTERNAL_INPUT_OWID_DIR, "covid_category_notes.csv")
INTERNAL_INPUT_UN_DIR = os.path.join(INTERNAL_INPUT_DIR, "un")
INTERNAL_INPUT_UN_POPULATION_FILE = os.path.join(INTERNAL_INPUT_UN_DIR, "population_latest.csv")
INTERNAL_INPUT_UN_POPULATION_AGE_FILE = os.path.join(INTERNAL_INPUT_UN_DIR, "population_age_latest.csv")
INTERNAL_INPUT_WB_DIR = os.path.join(INTERNAL_INPUT_DIR, "wb")
INTERNAL_INPUT_WB_INCOME_FILE = os.path.join(INTERNAL_INPUT_WB_DIR, "income_groups.csv")
INTERNAL_INPUT_SWEDEN_DIR = os.path.join(INTERNAL_INPUT_DIR, "sweden")
INTERNAL_INPUT_SWEDEN_DEATHS_FILE = os.path.join(INTERNAL_INPUT_SWEDEN_DIR, "sweden_deaths_per_day.csv")
### Input cases/deaths
INTERNAL_INPUT_WHO_DIR = os.path.join(INTERNAL_INPUT_DIR, "who")
INTERNAL_INPUT_WHO_CASES_DEATHS_COUNTRY_STD_FILE = os.path.join(
    INTERNAL_INPUT_WHO_DIR, "cases_deaths.countries_mapping.json"
)
### Input templates
INTERNAL_INPUT_TEMPLATE = os.path.join(INTERNAL_INPUT_DIR, "templates")
INTERNAL_INPUT_TEMPLATE_STATUS = os.path.join(INTERNAL_INPUT_TEMPLATE, "status.md")

### Input vax
INTERNAL_INPUT_VAX_DIR = os.path.join(INTERNAL_INPUT_DIR, "vax")
INTERNAL_INPUT_VAX_COUNTRIES_FILE = os.path.join(INTERNAL_INPUT_VAX_DIR, "countries.csv")

## Grapher
INTERNAL_GRAPHER_DIR = os.path.join(INTERNAL_DIR, "grapher")
INTERNAL_GRAPHER_BSG_FILE = os.path.join(INTERNAL_GRAPHER_DIR, "COVID Government Response (OxBSG).csv")
INTERNAL_GRAPHER_VAX_US_FILE = os.path.join(INTERNAL_GRAPHER_DIR, "COVID-19 - United States vaccinations.csv")

## Temporary
INTERNAL_TMP_VAX_MAIN_FILE = os.path.join(INTERNAL_DIR, "vaccinations.preliminary.csv")
INTERNAL_TMP_VAX_META_FILE = os.path.join(INTERNAL_DIR, "metadata.preliminary.csv")

## Status
INTERNAL_STATUS_FILE = os.path.join(INTERNAL_OUTPUT_DIR, "STATUS.md")


# CONFIG ################################
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "owid")
"""Where temporary files are stored."""
CONFIG_FILE = os.environ.get("OWID_COVID_CONFIG", os.path.join(PROJECT_DIR, "scripts/config.yaml"))
"""YAML with pipeline & execution configuration. Obtained from env var $OWID_COVID_CONFIG."""
if CONFIG_FILE is None:
    raise EnvironmentError(
        "Environment variable 'OWID_COVID_CONFIG' not set up. Please set it to the path of your configuration file."
    )
elif not os.path.isfile(CONFIG_FILE):
    raise EnvironmentError(
        f"Environment variable 'OWID_COVID_CONFIG' is pointing to an inexisting file {CONFIG_FILE}. Make sure that the"
        " file exists."
    )
SECRETS_FILE = os.environ.get("OWID_COVID_SECRETS", os.path.join(PROJECT_DIR, "scripts/secrets.yaml"))
"""YAML with secrets, links and credentials. Not shared publicly. Obtained from env var $OWID_COVID_SECRETS."""
if SECRETS_FILE is None:
    raise EnvironmentError(
        "Environment variable 'OWID_COVID_SECRETS' not set up. Please set it to the path of your secrets file."
    )
########################################################################################################################


def out_vax(country: str, public=False, age=False, manufacturer=False, proposal=False):
    if not public:
        if age:
            return os.path.join(INTERNAL_OUTPUT_VAX_AGE_DIR, f"{country}.csv")
        elif manufacturer:
            return os.path.join(INTERNAL_OUTPUT_VAX_MANUFACT_DIR, f"{country}.csv")
        elif proposal:
            return os.path.join(INTERNAL_OUTPUT_VAX_PROPOSALS_DIR, f"{country}.csv")
        return os.path.join(INTERNAL_OUTPUT_VAX_MAIN_DIR, f"{country}.csv")
    else:
        return os.path.join(DATA_VAX_COUNTRY_DIR, f"{country}.csv")

import click

from cowidev.cmd.commons.get import main_get_data
from cowidev.cmd.commons.utils import Country2Module, PythonLiteralOption
from cowidev.utils.params import CONFIG
from cowidev.utils import paths
from cowidev.vax.countries import MODULES_NAME, MODULES_NAME_BATCH, MODULES_NAME_INCREMENTAL, country_to_module


@click.command(name="get", short_help="Step 1: Scrape vaccination data from primary sources.")
# @click.option(
#     "--countries",
#     "-c",
#     default=CONFIG.pipeline.vaccinations.get.countries,
#     # default=[],
#     help="List of countries to skip (comma-separated)",
#     cls=PythonLiteralOption,
# )
@click.argument(
    "countries",
    nargs=-1,
    # help="List of countries to skip (comma-separated)",
    # default=CONFIG.pipeline.vaccinations.get.countries,
)
@click.option(
    "--skip-countries",
    "-s",
    default=CONFIG.pipeline.vaccinations.get.skip_countries,
    help="List of countries to skip (comma-separated)",
    cls=PythonLiteralOption,
)
@click.option(
    "--optimize/--no-optimize",
    "-O",
    default=False,
    help="Optimize processes based on older logging times.",
    show_default=True,
)
@click.pass_context
def click_vax_get(ctx, countries, skip_countries, optimize):
    """Runs scraping scripts to collect the data from the primary sources of COUNTRIES. Data is exported to project
    folder scripts/output/vaccinations/. By default, all countries are scraped.

    By default, the default values for OPTIONS are those specified in the configuration file. The configuration file is
    a YAML file with the pipeline settings. Note that the environment variable `OWID_COVID_CONFIG` must be pointing to
    this file. We provide a default config file in the project folder scripts/config.yaml.

    OPTIONS passed via command line will overwrite those from configuration file.

    Examples:

        Run the step using default values, from config.yaml file: `cowid vax get`

        Run the step only for Australia: `cowid vax get australia`

        Run the step for all countries except Australia: `cowid vax get -s australia all`

        Run the step for all incremental processes (can be also done using 'batch'): `cowid vax get incremental`
    """
    if countries == ():
        countries = CONFIG.pipeline.vaccinations.get.countries
    c2m = Country2Module(
        modules_name=MODULES_NAME,
        modules_name_incremental=MODULES_NAME_INCREMENTAL,
        modules_name_batch=MODULES_NAME_BATCH,
        country_to_module=country_to_module,
    )
    modules = c2m.parse(countries)
    modules_skip = c2m.parse(skip_countries)
    report_msg = main_get_data(
        modules_valid=MODULES_NAME,
        parallel=ctx.obj["parallel"],
        n_jobs=ctx.obj["n_jobs"],
        modules=modules,
        modules_skip=modules_skip,
        log_header="VAX",
        log_s3_path="s3://covid-19/log/vax-get-data-countries.csv" if optimize else None,
        output_status=paths.INTERNAL_OUTPUT_VAX_STATUS_GET,
        output_status_ts=paths.INTERNAL_OUTPUT_VAX_STATUS_GET_TS,
        logger=ctx.obj["logger"],
    )
    if ctx.obj["server"]:
        report_msg.to_slack()
        print(report_msg)

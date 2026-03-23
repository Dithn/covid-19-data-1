import click

from cowidev.cmd.commons.utils import (
    Country2Module,
    OrderedGroup,
    PythonLiteralOption,
    feedback_log,
)
from cowidev.hosp.countries import MODULES_NAME, country_to_module
from cowidev.hosp.etl import run_etl
from cowidev.hosp.grapher import run_grapheriser
from cowidev.utils.params import CONFIG


@click.group(name="hosp", chain=True, cls=OrderedGroup)
@click.pass_context
def click_hosp(ctx):
    """COVID-19 Hospitalization data pipeline."""
    pass


@click.command(name="generate", short_help="Step 1: Get and generate hospitalization dataset.")
@click.argument(
    "countries",
    nargs=-1,
    # help="List of countries to skip (comma-separated)",
    # default=CONFIG.pipeline.vaccinations.get.countries,
)
@click.option(
    "--skip-countries",
    "-s",
    default=CONFIG.pipeline.hospitalizations.generate.skip_countries,
    help="List of countries to skip (comma-separated)",
    cls=PythonLiteralOption,
)
@click.pass_context
def click_hosp_generate(ctx, countries, skip_countries):
    """Runs scraping scripts to collect the data from the primary sources, transforms it and exports the result to
    public/data/hospitalizations/.

    By default, the default values for OPTIONS are those specified in the configuration file. The configuration file is
    a YAML file with the pipeline settings. Note that the environment variable `OWID_COVID_CONFIG` must be pointing to
    this file. We provide a default config file in the project folder scripts/config.yaml.

    OPTIONS passed via command line will overwrite those from configuration file.
    """
    if countries == ():
        countries = CONFIG.pipeline.hospitalizations.generate.countries
    c2m = Country2Module(
        modules_name=MODULES_NAME,
        country_to_module=country_to_module,
    )
    modules = c2m.parse(countries)
    modules_skip = c2m.parse(skip_countries)
    feedback_log(
        func=run_etl,
        parallel=ctx.obj["parallel"],
        n_jobs=ctx.obj["n_jobs"],
        modules=modules,
        modules_skip=modules_skip,
        server=ctx.obj["server"],
        domain="Hospitalizations",
        step="generate",
        text_success="Hospitalization files were correctly generated.",
    )


@click.command(name="grapher-io", short_help="Step 2: Generate grapher-ready files.")
@click.pass_context
def click_hosp_grapherio(ctx):
    feedback_log(
        func=run_grapheriser,
        server=ctx.obj["server"],
        domain="Hospitalizations",
        step="grapher-io",
        text_success="Hospitalization Grapher files were correctly generated.",
    )


click_hosp.add_command(click_hosp_generate)
click_hosp.add_command(click_hosp_grapherio)

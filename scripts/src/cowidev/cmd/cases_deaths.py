import click

from cowidev.cases_deaths import generate_dataset
from cowidev.cmd.commons.utils import OrderedGroup, feedback_log


@click.group(name="casedeath", chain=True, cls=OrderedGroup)
@click.pass_context
def click_cases_deaths(ctx):
    """COVID-19 Cases/Deaths data pipeline."""
    pass


@click.command(name="generate", short_help="Step 1: Generate dataset.")
@click.pass_context
def click_cd_generate(ctx):
    feedback_log(
        func=generate_dataset,
        server=ctx.obj["server"],
        server_mode=ctx.obj["server"],
        domain="Cases/Deaths",
        step="generate",
        text_success="Public data files generated.",
        logger=ctx.obj["logger"],
    )


click_cases_deaths.add_command(click_cd_generate)

import click

from cowidev.cmd.commons.utils import OrderedGroup, feedback_log
from cowidev.xm.etl import run_etl


@click.group(name="xm", chain=True, cls=OrderedGroup)
@click.pass_context
def click_xm(ctx):
    """COVID-19 Excess Mortality data pipeline."""
    pass


@click.command(name="generate", short_help="Step 1: Get and generate hospitalization dataset.")
@click.pass_context
def click_xm_generate(ctx):
    """Download and generate our COVID-19 Hospitalization dataset."""
    feedback_log(
        func=run_etl,
        server=ctx.obj["server"],
        domain="Excess Mortality",
        step="generate",
        text_success="Excess Mortality files generated.",
    )


click_xm.add_command(click_xm_generate)

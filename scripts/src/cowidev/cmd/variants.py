import click

from cowidev.cmd.commons.utils import OrderedGroup, feedback_log
from cowidev.variants.etl import run_etl
from cowidev.variants.grapher import run_grapheriser, run_explorerizer


@click.group(name="variants", chain=True, cls=OrderedGroup)
@click.pass_context
def click_variants(ctx):
    """COVID-19 Variants data pipeline."""
    pass


@click.command(name="generate", short_help="Step 1: Get and generate hospitalization dataset.")
@click.pass_context
def click_variants_generate(ctx):
    """Download and generate our COVID-19 Hospitalization dataset."""
    feedback_log(
        func=run_etl,
        server=ctx.obj["server"],
        domain="Variants",
        step="generate",
        hide_success=True,
    )


@click.command(name="grapher-io", short_help="Step 2: Generate grapher-ready files.")
@click.pass_context
def click_variants_grapherio(ctx):
    def _function():
        run_grapheriser()
        run_explorerizer()

    feedback_log(
        func=_function,
        server=ctx.obj["server"],
        domain="Variants",
        step="generate",
        hide_success=True,
    )


click_variants.add_command(click_variants_generate)
click_variants.add_command(click_variants_grapherio)

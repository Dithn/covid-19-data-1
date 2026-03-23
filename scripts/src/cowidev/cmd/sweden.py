import click

from cowidev.cmd.commons.utils import OrderedGroup, feedback_log
from cowidev.sweden import download_data, generate_dataset


@click.group(name="sweden", chain=True, cls=OrderedGroup)
@click.pass_context
def click_sweden(ctx):
    """COVID-19 Sweden data pipeline."""
    pass


@click.command(name="get", short_help="Step 1: Get file for Sweden dataset.")
@click.pass_context
def click_sweden_get(ctx):
    """Download source file for Sweden dataset."""
    feedback_log(
        func=download_data,
        server=ctx.obj["server"],
        domain="Sweden",
        step="get",
        hide_success=True,
        text_success="Sweden file downloaded.",
    )


@click.command(name="generate", short_help="Step 2: Generate Sweden dataset.")
@click.pass_context
def click_sweden_generate(ctx):
    """Generate our COVID-19 Sweden dataset."""
    feedback_log(
        func=generate_dataset,
        server=ctx.obj["server"],
        domain="Sweden",
        step="generate",
        text_success="Sweden files generated.",
    )


click_sweden.add_command(click_sweden_get)
click_sweden.add_command(click_sweden_generate)

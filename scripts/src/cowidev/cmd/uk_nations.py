import click

from cowidev.cmd.commons.utils import OrderedGroup, feedback_log
from cowidev.uk_nations import generate_dataset


@click.group(name="uk-nations", chain=True, cls=OrderedGroup)
@click.pass_context
def click_uk_nations(ctx):
    """COVID-19 UK Nations data pipeline."""
    pass


@click.command(name="generate", short_help="Step 1: Get and generate UK Nations dataset.")
@click.pass_context
def click_uk_get(ctx):
    """Generate dataset."""
    feedback_log(
        func=generate_dataset,
        server=ctx.obj["server"],
        domain="UK Nations",
        step="generate",
        hide_success=True,
    )


click_uk_nations.add_command(click_uk_get)

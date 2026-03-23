import click

from cowidev import PATHS
from cowidev.vax.us_states import run_etl, run_grapheriser
from cowidev.cmd.commons.utils import feedback_log


@click.command(name="us-states", short_help="US vaccinations data pipeline.")
@click.pass_context
def click_vax_us(ctx):
    def _function():
        run_etl(PATHS.DATA_VAX_US_FILE)
        run_grapheriser(PATHS.DATA_VAX_US_FILE, PATHS.INTERNAL_GRAPHER_VAX_US_FILE)

    feedback_log(
        func=_function,
        server=ctx.obj["server"],
        domain="Vaccinations",
        step="us-states",
        text_success="Vaccination data for US states was updated.",
    )

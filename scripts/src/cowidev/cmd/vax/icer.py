import click

from cowidev.vax.icer import main
from cowidev.cmd.commons.utils import feedback_log


@click.command(
    name="icer", short_help="Download some specific country files. Useful when these are very large in size."
)
@click.pass_context
def click_vax_icer(ctx):
    feedback_log(
        func=main,
        logger=ctx.obj["logger"],
        server=ctx.obj["server"],
        domain="Vaccinations",
        step="icer",
        hide_success=True,
    )

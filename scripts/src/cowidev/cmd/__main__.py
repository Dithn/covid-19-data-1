import click

from cowidev.utils.params import CONFIG
from cowidev.utils.log import get_logger
from cowidev.cmd.commons.utils import OrderedGroup
from cowidev.cmd.testing import click_test
from cowidev.cmd.vax import click_vax
from cowidev.cmd.hosp import click_hosp
from cowidev.cmd.cases_deaths import click_cases_deaths
from cowidev.cmd.xm import click_xm
from cowidev.cmd.variants import click_variants
from cowidev.cmd.megafile import click_megafile
from cowidev.cmd.sweden import click_sweden
from cowidev.cmd.uk_nations import click_uk_nations
from cowidev.cmd.check import click_check


@click.group(name="cowid", cls=OrderedGroup)
@click.option(
    "--parallel/--no-parallel",
    default=CONFIG.execution.parallel,
    help="Parallelize process.",
    show_default=True,
)
@click.option(
    "--n-jobs",
    default=CONFIG.execution.njobs,
    type=int,
    help="Number of threads to use.",
    show_default=True,
)
@click.option(
    "--server/--no-server",
    "-S",
    default=False,
    help="Only critical log and final message to slack.",
    show_default=True,
)
@click.pass_context
def cli(ctx, parallel, n_jobs, server):
    """COVID-19 Data pipeline tool by Our World in Data."""
    ctx.ensure_object(dict)
    ctx.obj["parallel"] = parallel
    ctx.obj["n_jobs"] = n_jobs
    ctx.obj["server"] = server
    if ctx.obj["server"]:
        ctx.obj["logger"] = get_logger("critical")
    else:
        ctx.obj["logger"] = get_logger()


cli.add_command(click_megafile)
cli.add_command(click_test)
cli.add_command(click_vax)
cli.add_command(click_hosp)
cli.add_command(click_cases_deaths)
cli.add_command(click_variants)
cli.add_command(click_xm)
cli.add_command(click_sweden)
cli.add_command(click_uk_nations)
cli.add_command(click_check)


if __name__ == "__main__":
    cli()

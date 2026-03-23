import click

from cowidev.cmd.commons.utils import OrderedGroup
from cowidev.cmd.vax.get import click_vax_get
from cowidev.cmd.vax.process import click_vax_process
from cowidev.cmd.vax.generate import click_vax_generate
from cowidev.cmd.vax.export import click_vax_export
from cowidev.cmd.vax.track import click_vax_track
from cowidev.cmd.vax.icer import click_vax_icer
from cowidev.cmd.vax.us import click_vax_us


@click.group(name="vax", chain=True, cls=OrderedGroup)
@click.pass_context
def click_vax(ctx):
    """COVID-19 Vaccination data pipeline."""
    pass


click_vax.add_command(click_vax_get)
click_vax.add_command(click_vax_process)
click_vax.add_command(click_vax_generate)
click_vax.add_command(click_vax_export)
click_vax.add_command(click_vax_track)
click_vax.add_command(click_vax_icer)
click_vax.add_command(click_vax_us)

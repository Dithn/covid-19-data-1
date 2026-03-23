import click
from cowidev.megafile.generate import generate_megafile
from cowidev.cmd.commons.utils import feedback_log


@click.command(name="megafile")
@click.pass_context
def click_megafile(ctx):
    """COVID-19 data integration pipeline (former megafile)"""
    feedback_log(
        func=generate_megafile,
        logger=ctx.obj["logger"],
        server=ctx.obj["server"],
        domain="Megafile",
        text_success="Public data files generated.",
        hide_success=True,
    )

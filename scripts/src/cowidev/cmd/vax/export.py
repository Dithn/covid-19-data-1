import click

from cowidev.megafile.generate import generate_megafile
from cowidev.cmd.commons.utils import StepReport
from cowidev.utils.utils import get_traceback


@click.command(name="export", short_help="Step 4: Export vaccination data and merge with global dataset.")
@click.pass_context
def click_vax_export(ctx):
    try:
        ctx.obj["logger"].info("-- Generating megafiles... --")
        generate_megafile(ctx.obj["logger"])
    except Exception as err:
        if ctx.obj["server"]:
            StepReport(
                title="Vaccinations - [export] step failed",
                trace=get_traceback(err),
                type="error",
            ).to_slack()
        else:
            raise err
    else:
        if ctx.obj["server"]:
            StepReport(
                title="Vaccinations - [export] step ran successfully",
                text="Megafile generated, source table updated.",
                type="success",
            ).to_slack()

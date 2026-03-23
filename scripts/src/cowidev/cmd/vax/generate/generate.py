import click

from cowidev.cmd.vax.generate.utils import DatasetGenerator
from cowidev.cmd.commons.utils import StepReport
from cowidev.utils.utils import get_traceback


@click.command(name="generate", short_help="Step 3: Generate vaccination dataset.")
@click.pass_context
def click_vax_generate(ctx):
    # Select columns
    generator = DatasetGenerator(ctx.obj["logger"])
    try:
        generator.run()
    except Exception as err:
        if ctx.obj["server"]:
            StepReport(
                title="Vaccinations - [generate] step failed",
                trace=get_traceback(err),
                type="error",
            ).to_slack()
        else:
            raise err
    else:
        if ctx.obj["server"]:
            StepReport(
                title="Vaccinations - [generate] step ran successfully",
                text="Intermediate vaccinations files were correctly generated.",
                type="success",
            ).to_slack()

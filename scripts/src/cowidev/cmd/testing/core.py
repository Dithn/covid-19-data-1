import click
from cowidev.cmd.testing.get import click_test_get


@click.group(name="test", chain=True)
@click.pass_context
def click_test(ctx):
    """COVID-19 Testing data pipeline."""
    pass


click_test.add_command(click_test_get)

import os

import click

from cowidev.cmd.vax.track.countries import country_updates_summary


@click.command(name="track", short_help="Explore high-level analytics of vaccination dataset.")
@click.option("--output", default="cowid-vax-track.report.tmp.csv", show_default=True, help="Output CSV file.")
@click.option(
    "--disable-export", "-d", default=False, show_default=True, help="Do not export CSV file, just logging results."
)
def click_vax_track(output, disable_export):
    df = country_updates_summary(sortby_updatefreq=True, who=True, vaccines=True, metric_counts=True)
    if not disable_export:
        export_to_csv(df, filename=output)
    print(df.head())


def export_to_csv(df, filename):
    filename = os.path.abspath(filename)
    df.to_csv(filename, index=False)
    print(f"Data exported to {filename}")
    print()

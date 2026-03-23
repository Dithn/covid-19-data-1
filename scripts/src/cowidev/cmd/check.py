import datetime
import pytz
import os
import pandas as pd

import click

from cowidev.cmd.commons.utils import OrderedGroup, feedback_log


CASES_DEATHS_URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/cases_deaths/full_data.csv"
VAX_URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/vaccinations.csv"
TESTING_URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/testing/covid-testing-all-observations.csv"
HOSP_URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/hospitalizations/covid-hospitalizations.csv"
FULL_URL_CSV = "https://covid.ourworldindata.org/data/owid-covid-data.csv"
FULL_URL_XLSX = "https://covid.ourworldindata.org/data/owid-covid-data.xlsx"
# FULL_URL_JSON = "https://covid.ourworldindata.org/data/owid-covid-data.json"

# ALLOWED DAYS
ALLOWED_DAYS_MAX_VAX = 20
ALLOWED_DAYS_MAX_CASESDEATHS = 30
ALLOWED_DAYS_MAX_JHU = 20
ALLOWED_DAYS_MAX_TESTING = 20
ALLOWED_DAYS_MAX_HOSP = 20
ALLOWED_DAYS_MAX_MEGAFILE = 10


def check_updated(url, date_col, allowed_days, weekends, local_check=False, url_local=None) -> None:
    if not weekends and datetime.datetime.today().weekday() in [5, 6]:
        print("Today is a weekend, skipping...")
        return
    if url.endswith(".csv"):
        df = pd.read_csv(url)
    elif url.endswith(".xlsx"):
        df = pd.read_excel(url)
    max_date = df[date_col].max()
    if max_date < str(datetime.date.today() - datetime.timedelta(days=allowed_days)):
        raise Exception(
            f"Data is not updated (exceeded maximum allowed days of {allowed_days})! Last date is {max_date}. "
            "Please check if something is broken in our pipeline and/or if someone is in charge of today's "
            f"update. URL is '{url}'"
        )
    if local_check:
        url = url_local if url_local else url
        filepath = url.split("https://raw.githubusercontent.com/owid/covid-19-data/master/")[-1]
        statbuf = os.stat(filepath)
        ts_modified = datetime.datetime.fromtimestamp(statbuf.st_mtime, pytz.utc)
        if (diff_sec := (datetime.datetime.now(pytz.utc) - ts_modified).total_seconds()) > (
            max_sec := allowed_days * (60 * 60 * 24)
        ):
            raise Exception(
                f"File was modified more than {allowed_days} days: `{diff_sec} sec > {max_sec} sec `! "
                f"Last modification date is {ts_modified.strftime('%X %x')}. Check if something is broken in our "
                f"pipeline and/or if someone is in charge of today's update. File is '{filepath}'"
            )
    print("Check passed. All good!")


@click.group(name="check", chain=True, cls=OrderedGroup)
@click.pass_context
def click_check(ctx):
    """COVID-19 data pipeline checks."""
    pass


@click.command(name="vax", short_help="Vaccination data.")
@click.pass_context
def click_check_vax(ctx):
    """Generate dataset."""
    feedback_log(
        func=check_updated,
        url=VAX_URL,
        date_col="date",
        allowed_days=ALLOWED_DAYS_MAX_VAX,
        weekends=False,
        server=ctx.obj["server"],
        domain="Check",
        step="vaccinations",
        hide_success=True,
        channel="covid-19",
    )


@click.command(name="casedeath", short_help="Cases/Death data.")
@click.pass_context
def click_check_casedeath(ctx):
    """Upload dataset to DB."""
    feedback_log(
        func=check_updated,
        url=CASES_DEATHS_URL,
        date_col="date",
        allowed_days=ALLOWED_DAYS_MAX_CASESDEATHS,
        weekends=True,
        server=ctx.obj["server"],
        domain="Check",
        step="casedeath",
        hide_success=True,
        local_check=True,
        channel="covid-19",
    )


@click.command(name="test", short_help="Testing data.")
@click.pass_context
def click_check_test(ctx):
    """Upload dataset to DB."""
    feedback_log(
        func=check_updated,
        url=TESTING_URL,
        date_col="Date",
        allowed_days=ALLOWED_DAYS_MAX_TESTING,
        weekends=False,
        server=ctx.obj["server"],
        domain="Check",
        step="vaccinations",
        hide_success=True,
        channel="covid-19",
    )


@click.command(name="hosp", short_help="Hospital & ICU data.")
@click.pass_context
def click_check_hosp(ctx):
    """Upload dataset to DB."""
    feedback_log(
        func=check_updated,
        url=HOSP_URL,
        date_col="date",
        allowed_days=ALLOWED_DAYS_MAX_HOSP,
        weekends=True,
        server=ctx.obj["server"],
        domain="Check",
        step="hospital",
        hide_success=True,
        channel="covid-19",
    )


@click.command(name="megafile", short_help="Complete dataset.")
@click.pass_context
def click_check_megafile(ctx):
    """Upload dataset to DB."""
    # CSV file
    feedback_log(
        func=check_updated,
        url=FULL_URL_CSV,
        date_col="date",
        allowed_days=ALLOWED_DAYS_MAX_MEGAFILE,
        weekends=True,
        server=ctx.obj["server"],
        domain="Check",
        step="megafile",
        hide_success=True,
        channel="covid-19",
    )
    # XLSX file
    feedback_log(
        func=check_updated,
        url=FULL_URL_XLSX,
        date_col="date",
        allowed_days=ALLOWED_DAYS_MAX_MEGAFILE,
        weekends=True,
        server=ctx.obj["server"],
        domain="Check",
        step="megafile",
        hide_success=True,
        channel="covid-19",
    )

    # JSON file
    # feedback_log(
    #     func=check_updated,
    #     url=FULL_URL_JSON,
    #     date_col="date",
    #     allowed_days=1,
    #     weekends=True,
    #     server=ctx.obj["server"],
    #     domain="Check",
    #     step="megafile",
    #     hide_success=True,
    #     channel="covid-19",
    # )


click_check.add_command(click_check_vax)
click_check.add_command(click_check_test)
click_check.add_command(click_check_hosp)
click_check.add_command(click_check_casedeath)
click_check.add_command(click_check_megafile)

import pandas as pd

from cowidev.utils import clean_date
from cowidev.utils.log import get_logger
from cowidev.utils.web.download import read_csv_from_url
from cowidev.testing.utils.orgs import ECDC_COUNTRIES
from cowidev.testing.utils.base import CountryTestBase

logger = get_logger()


class ECDC(CountryTestBase):
    location: str = "ECDC"
    source_url_ref: str = "https://www.ecdc.europa.eu/en/publications-data/covid-19-testing"
    source_url: str = "https://opendata.ecdc.europa.eu/covid19/testing/csv/data.csv"
    source_label: str = "European Centre for Disease Prevention and Control (ECDC)"
    units: str = "tests performed"
    columns_use: list = [
        "year_week",
        "region_name",
        "tests_done",
    ]
    rename_columns = {
        "region_name": "location",
        "tests_done": "Cumulative total",
        "year_week": "Date",
    }

    def read(self):
        """Read data from source."""
        return read_csv_from_url(self.source_url, timeout=20)

    def _yearweek_to_date(self, year_week: str) -> str:
        """Convert year_week(yyyy-Www) to date."""
        date = clean_date(year_week + "+4", "%Y-W%W+%w")
        return date

    def pipe_rename_countries(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename countries to match OWID naming convention."""
        df["location"] = df.location.replace(ECDC_COUNTRIES)
        return df

    def pipe_filter_entries(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get valid entries:

        - Discard subnational data.
        - Countries not coming from OWID (avoid loop).
        """
        df = df[df.location.isin(ECDC_COUNTRIES.values())]
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipe to convert year_week to date."""
        return df.assign(Date=df.Date.apply(self._yearweek_to_date))

    def pipe_cumsum(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate cumulative sum of tests."""
        df = df.assign(**{"Cumulative total": df.groupby(["location"])["Cumulative total"].cumsum()})
        return df.drop_duplicates(subset="Date")

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add metadata to DataFrame."""
        mapping = {
            "Country": df["location"],
            "Units": self.units,
            "Notes": self.notes,
            "Source URL": self.source_url_ref,
            "Source label": self.source_label,
        }
        mapping = {k: v for k, v in mapping.items() if k not in df}
        self._check_attributes(mapping)
        return df.assign(**mapping)

    def pipeline(self, df: pd.DataFrame):
        """Pipeline for data."""
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_rename_countries)
            .pipe(self.pipe_filter_entries)
            .pipe(self.pipe_date)
            .pipe(self.pipe_cumsum)
            .pipe(self.pipe_metadata)
        )

    def export_countries(self, df: pd.DataFrame):
        """Export data to the relevant csv and log the confirmation."""
        locations = set(df.location)
        for location in locations:
            df_c = df[df.location == location]
            df_c = df_c.dropna(
                subset=["Cumulative total"],
                how="all",
            )
            if not df_c.empty:
                self.export_datafile(df_c, filename=location)
                logger.info(f"\tcowidev.testing.batch.ecdc.{location}: SUCCESS ✅")

    def export(self):
        """Export data to CSV."""
        df = self.read().pipe(self.pipeline)
        self.export_countries(df)


def main():
    ECDC().export()

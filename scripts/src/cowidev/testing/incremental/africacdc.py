from datetime import datetime
import os

import pandas as pd

from cowidev.utils.clean import clean_date
from cowidev.utils.web import request_json
from cowidev.utils.log import get_logger
from cowidev import PATHS
from cowidev.testing.utils.orgs import ACDC_COUNTRIES
from cowidev.testing.utils.base import CountryTestBase

logger = get_logger()


class AfricaCDC(CountryTestBase):
    location: str = "ACDC"  # Arbitrary location to pass checks
    units: str = "tests performed"
    _base_url = (
        "https://services8.arcgis.com/vWozsma9VzGndzx7/ArcGIS/rest/services/"
        "DailyCOVIDDashboard_5July21_1/FeatureServer/0/"
    )
    source_url_ref: str = "https://africacdc.org/covid-19/"
    source_label: str = "Africa Centres for Disease Control and Prevention"
    date: str = None
    columns_use: list = [
        "Country",
        "Tests_Conducted",
    ]
    rename_columns: dict = {
        "Country": "location",
        "Tests_Conducted": "Cumulative total",
    }

    @property
    def source_url(self):
        return f"{self._base_url}/query?f=json&where=1=1&outFields=*"

    @property
    def source_url_date(self):
        return f"{self._base_url}?f=pjson"

    def read(self) -> pd.DataFrame:
        # Pull data from API
        data = request_json(self.source_url)
        df = self._parse_data(data)
        return df

    def _parse_data(self, data) -> pd.DataFrame:
        res = [d["attributes"] for d in data["features"]]
        df = pd.DataFrame(res)
        # Parse date
        self.date = self._parse_date()
        # Parse metrics
        df = self._parse_metrics(df)
        return df

    def pipe_filter_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[self.columns_use]

    def pipe_rename_countries(self, df: pd.DataFrame) -> pd.DataFrame:
        """Renames countries to match OWID naming convention."""
        df["location"] = df.location.replace(ACDC_COUNTRIES)
        return df

    def pipe_filter_entries(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Gets valid entries:

        - Countries not coming from OWID (avoid loop)
        """
        df = df[df.location.isin(ACDC_COUNTRIES.values())]
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(date=self._parse_date())

    def _parse_date(self) -> str:
        res = request_json(self.source_url_date)
        edit_ts = res["editingInfo"]["lastEditDate"]
        date = clean_date(datetime.fromtimestamp(edit_ts / 1000))
        return date

    def _parse_metrics(self, df: list) -> pd.DataFrame:
        df = df.loc[:, self.columns_use]
        return df

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Adds metadata to DataFrame"""
        mapping = {
            "Country": df["location"],
            "Units": self.units,
            "Notes": self.notes,
            "Source URL": self.source_url_ref,
            "Source label": self.source_label,
            "Date": self.date,
        }
        mapping = {k: v for k, v in mapping.items() if k not in df}
        self._check_attributes(mapping)
        return df.assign(**mapping)

    def increment_countries(self, df: pd.DataFrame):
        """Exports data to the relevant csv and logs the confirmation."""
        locations = set(df.location)
        df["Cumulative total"].replace(",", "", regex=True, inplace=True)
        df["Cumulative total"] = df["Cumulative total"].apply(pd.to_numeric, errors="coerce")
        for location in locations:
            df_c = df[df.location == location]
            df_c = df_c.dropna(
                subset=["Cumulative total"],
                how="all",
            )
            df_current = pd.read_csv(os.path.join(PATHS.INTERNAL_OUTPUT_TEST_MAIN_DIR, f"{location}.csv"))
            # Ensure that cumulative total has changed since last update
            if not df_c.empty and df_c["Cumulative total"].max() > df_current["Cumulative total"].max():
                self.export_datafile(df_c, filename=location, attach=True)
                logger.info(f"\tcowidev.testing.incremental.africacdc.{location}: SUCCESS ✅")

    def pipeline(self, df: pd.DataFrame):
        """Pipeline for data"""
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_rename_countries)
            .pipe(self.pipe_filter_entries)
            .pipe(self.pipe_metadata)
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.increment_countries(df)


def main():
    AfricaCDC().export()

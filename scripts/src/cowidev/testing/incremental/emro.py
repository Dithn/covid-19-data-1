import requests

from bs4 import BeautifulSoup
import pandas as pd
import tabula

from cowidev.utils import get_soup
from cowidev.utils.log import get_logger
from cowidev.utils.clean import extract_clean_date
from cowidev.testing.utils.orgs import EMRO_COUNTRIES
from cowidev.testing.utils.base import CountryTestBase

logger = get_logger()


class EMRO(CountryTestBase):
    location: str = "EMRO"  # Arbitrary location to pass checks
    units: str = "tests performed"
    source_url: str = "http://www.emro.who.int/health-topics/corona-virus/situation-reports.html"
    _base_url: str = "http://www.emro.who.int"
    source_label: str = "WHO Regional Office for the Eastern Mediterranean"
    date: str = None
    regex: dict = {
        "date": r"(\d{1,2} \w+ 20\d{2})",
    }
    columns_use: list = [
        "Country",
        "Total Tests",
    ]
    rename_columns: dict = {
        "Country": "location",
        "Total Tests": "Cumulative total",
    }
    columns_to_check: dict = {
        "tests": "Total Tests",
        "date": "Table 1: Epidemiological situation in the Eastern Mediterranean Region",
    }

    @property
    def area(Self) -> list:
        """
        Areas of pdf to be extracted

        Returns:
            list: [[y1, x1, y2, x2], ...]

        For more info see: https://github.com/tabulapdf/tabula-java/wiki/Using-the-command-line-tabula-extractor-tool
        """
        return [[56, 36, 98, 511], [119, 41, 488, 551]]

    def read(self) -> pd.DataFrame:
        """Reads data from source."""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parses data from soup"""
        # Obtain pdf url
        self.source_url_ref = self._parse_pdf_url(soup)
        # Extract data table
        df_list = self._parse_pdf_table()
        # Parse date
        self.date = self._parse_date(df_list)
        # Parse metrics
        df = self._parse_metrics(df_list)
        return df

    def _parse_pdf_url(self, soup: BeautifulSoup) -> str:
        """Parses pdf url from soup"""
        elem = soup.find(class_="download").find("a")
        if not elem:
            raise ValueError("Element not found, please update the script")
        href = elem.get("href")
        return f"{self._base_url}{href}"

    def _parse_pdf_table(self) -> list:
        """Parses pdf table"""
        response = requests.get(self.source_url_ref, stream=True, verify=True)
        df_list = tabula.read_pdf(response.raw, pages="all", area=self.area)
        return df_list

    def _parse_date(self, df_list: list) -> str:
        """Parses date from DataFrame list"""
        df_date = [df for df in df_list if self.columns_to_check["date"] in df.columns][0]
        date_str = df_date.iat[0, 0]
        date = extract_clean_date(date_str.lower(), regex=self.regex["date"], date_format="%d %B %Y")
        return date

    def _parse_metrics(self, df_list: list) -> pd.DataFrame:
        """Parses metrics from DataFrame list"""
        df = [table for table in df_list if self.columns_to_check["tests"] in table.columns][0]
        df = df.loc[:, self.columns_use]
        df.loc[:, self.columns_to_check["tests"]] = df.loc[:, self.columns_to_check["tests"]].str.replace(" ", "")
        df.loc[:, self.columns_to_check["tests"]] = pd.to_numeric(df.loc[:, self.columns_to_check["tests"]])
        return df

    def pipe_rename_countries(self, df: pd.DataFrame) -> pd.DataFrame:
        """Renames countries to match OWID naming convention."""
        df["location"] = df.location.replace(EMRO_COUNTRIES)
        return df

    def pipe_filter_entries(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Gets valid entries:

        - Countries not coming from OWID (avoid loop)
        """
        df = df[df.location.isin(EMRO_COUNTRIES.values())]
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
        for location in locations:
            df_c = df[df.location == location]
            df_c = df_c.dropna(
                subset=["Cumulative total"],
                how="all",
            )
            if not df_c.empty:
                self.export_datafile(df_c, filename=location, attach=True)
                logger.info(f"\tcowidev.testing.incremental.emro.{location}: SUCCESS ✅")

    def pipeline(self, df: pd.DataFrame):
        """Pipeline for data"""
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_rename_countries)
            .pipe(self.pipe_filter_entries)
            .pipe(self.pipe_metadata)
        )

    def export(self):
        """Exports data to csv."""
        df = self.read().pipe(self.pipeline)
        self.increment_countries(df)


def main():
    EMRO().export()

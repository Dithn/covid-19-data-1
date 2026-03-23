import time
from datetime import datetime

from selenium.webdriver.chrome.webdriver import WebDriver
import pandas as pd

from cowidev.utils.web import get_driver
from cowidev.utils.clean import clean_count, clean_date
from cowidev.testing import CountryTestBase


class Kosovo(CountryTestBase):
    location: str = "Kosovo"
    units: str = "tests performed"
    source_label: str = "National Institute of Public Health of Kosovo"
    source_url: str = (
        "https://datastudio.google.com/embed/u/0/reporting/2e546d77-8f7b-4c35-8502-38533aa0e9e8/page/tI3oB"
    )
    source_url_ref: str = "https://datastudio.google.com/embed/u/0/reporting/2e546d77-8f7b-4c35-8502-38533aa0e9e8"
    regex: dict = {
        "date": "Përditësimi i fundit:",
        "count": "Gjithsej të testuar",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        with get_driver() as driver:
            driver.get(self.source_url)
            time.sleep(10)
            df = self._parse_data(driver)
        return df

    def _parse_data(self, driver: WebDriver) -> pd.DataFrame:
        """Parse data from source"""
        # Extract data
        for block in driver.find_elements_by_class_name("kpimetric"):
            if self.regex["count"] in block.find_element_by_class_name("kpi-label").text:
                count = clean_count(block.find_element_by_class_name("valueLabel").text)
        for block in driver.find_elements_by_class_name("cell"):
            if self.regex["date"] in block.text:
                date_str = block.text

        if not count or not date_str:
            raise ValueError("Count or date not found, please update the script")
        # Parse data
        date = self._parse_date(date_str)
        # Create dataframe
        df = pd.DataFrame(
            {
                "Date": [date],
                "Cumulative total": [count],
            }
        )
        return df

    def _parse_date(self, date: str) -> str:
        """Parse date from soup"""
        day_month = date.split("Përditësimi i fundit:")[1].strip().lower()
        year = datetime.now().year
        date = f"{day_month} {year}"
        return clean_date(date, "%d %B %Y")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_metadata)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Kosovo().export()

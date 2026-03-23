import re

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
import pandas as pd

from cowidev.utils.web import get_driver
from cowidev.utils.clean import clean_count, clean_date
from cowidev.testing.utils.incremental import increment
from cowidev.testing.utils.base import CountryTestBase


class Croatia(CountryTestBase):
    location = "Croatia"
    units = "people tested"
    source_label = "Government of Croatia"
    source_url_ref = "https://www.koronavirus.hr/najnovije/ukupno-dosad-382-zarazene-osobe-u-hrvatskoj/35"
    regex = {
        "count": r"Do danas je ukupno testirano ([\d\.]+) osoba",
        "date": r"Objavljeno: ([\d\.]{10})",
    }

    def read(self) -> pd.Series:
        """Read data from source."""
        with get_driver() as driver:
            driver.get(self.source_url_ref)
            data = self._parse_data(driver)
        return pd.Series(data)

    def _parse_data(self, driver: WebDriver) -> dict:
        """Get data from the source page."""
        # Get relevant element
        elem = self._get_relevant_element(driver)
        # Get text from element
        text = self._get_text_from_element(elem)
        # Get date from text
        date = self._parse_date_from_text(text)
        # Get metrics from text
        count = self._parse_metrics(text)
        record = {
            "date": date,
            "count": count,
        }
        return record

    def _get_relevant_element(self, driver: WebDriver) -> WebElement:
        """Get the relevant element"""
        elem = driver.find_element_by_tag_name("body")
        if not elem:
            raise ValueError("No relevant element found, please check the source.")
        return elem

    def _get_text_from_element(self, elem: WebElement) -> str:
        """Extract text from the element."""
        return elem.text

    def _parse_date_from_text(self, text: str) -> str:
        """Get date from text."""
        date = re.search(self.regex["date"], text).group(1)
        return clean_date(date, "%d.%m.%Y")

    def _parse_metrics(self, text: str) -> int:
        """Get metrics from text."""
        count = re.search(self.regex["count"], text).group(1)
        return clean_count(count)

    def export(self):
        data = self.read()
        increment(
            sheet_name=self.location,
            country=self.location,
            units=self.units,
            date=data["date"],
            source_url=self.source_url_ref,
            source_label=self.source_label,
            count=data["count"],
        )


def main():
    Croatia().export()

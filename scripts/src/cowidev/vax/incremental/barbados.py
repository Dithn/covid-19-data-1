from multiprocessing.sharedctypes import Value
import re

from bs4 import BeautifulSoup
import pandas as pd

from cowidev.utils import get_soup, clean_count, clean_date
from cowidev.vax.utils.base import CountryVaxBase


class Barbados(CountryVaxBase):
    location: str = "Barbados"
    source_url: str = "https://gisbarbados.gov.bb/top-stories/"
    source_url_ref: str = None
    regex: dict = {
        "title": r"COVID-19 Update",
        "people_vaccinated": r"at least one dose is ([\d,\s]+)",
        # "people_vaccinated": r"COVID\-19, ([\d,\s]+) persons \(.*\) have received at least one dose",
        "people_fully_vaccinated": r"fully? (?:vaccinated|vaccinated persons) is ([\d,\s]+)",
        # "people_fully_vaccinated": (
        #     r"To date, ([\d,\s]+) individuals \– (?:[\d,\s]+) males and (?:[\d,\s]+) females \(.*\) \– have been fully"
        #     r" vaccinated"
        # ),
        # "people_vaccinated": (
        #     r"(\d+) persons \((?:[\d.]+) per cent of the eligible population\) have received at least one dose"
        # ),
        # "people_fully_vaccinated": (
        #     r"(\d+) individuals – (?:[\d]+) males and (?:[\d]+) females \((?:[\d.]+) per cent of the total"
        #     r" population or (?:[\d.]+) per cent of the eligible population\) are fully vaccinated"
        # ),
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from soup"""
        # Get the article URL
        elem = soup.find("a", text=re.compile(self.regex["title"]))
        if elem:
            link = elem["href"]
        else:
            raise ValueError("No COVID-19 update new was found!")
        if not link:
            raise ValueError("Article not found, please update the script")
        self.source_url_ref = link
        soup = get_soup(link)
        # Get the metrics
        metrics = self._parse_metrics(soup)
        # Get the date
        date = self._parse_date(soup)
        df = pd.DataFrame(
            {
                "date": [date],
                **metrics,
            }
        )
        return df

    def _parse_metrics(self, soup: BeautifulSoup) -> int:
        """Parse metrics from soup"""
        text = soup.get_text()
        text = re.sub(r"(\d),(\d)", r"\1\2", text)
        people_vaccinated = clean_count(re.search(self.regex["people_vaccinated"], text).group(1).replace(" ", ""))
        people_fully_vaccinated = clean_count(
            re.search(self.regex["people_fully_vaccinated"], text).group(1).replace(" ", "")
        )
        total_vaccinations = people_vaccinated + people_fully_vaccinated
        df = {
            "people_vaccinated": [people_vaccinated],
            "people_fully_vaccinated": [people_fully_vaccinated],
            "total_vaccinations": [total_vaccinations],
        }
        return df

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Parse date from soup"""
        date_str = soup.find(class_="published").text
        if not date_str:
            raise ValueError("Date not found, please update the script")
        return clean_date(date_str, "%b %d, %Y", minus_days=1)

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes vaccine names for main data."""
        return df.assign(vaccine="Oxford/AstraZeneca, Pfizer/BioNTech, Sinopharm/Beijing")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_metadata).pipe(self.pipe_vaccine)

    def export(self):
        """Export data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Barbados().export()

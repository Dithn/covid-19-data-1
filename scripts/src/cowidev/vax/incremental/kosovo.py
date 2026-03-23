from bs4 import BeautifulSoup
import pandas as pd

from cowidev.utils import get_soup, clean_count
from cowidev.utils.clean.dates import localdate
from cowidev.vax.utils.base import CountryVaxBase


class Kosovo(CountryVaxBase):
    location: str = "Kosovo"
    source_url: str = "https://msh.rks-gov.net/sq/statistikat-covid-19/"
    source_url_ref: str = "https://msh.rks-gov.net/sq/statistikat-covid-19/"
    regex: dict = {
        "Total": "Numri total i vaksinave të administruara",
        "Dose2": "Numri i të vaksinuarve me të dy dozat",
        "Dose3": "Numri i dozave të treta të administruara",
        "Boosters": "Numri i dozave përforcuese të administruara",
    }

    def read(self) -> pd.DataFrame:
        """Read data from source"""
        soup = get_soup(self.source_url, verify=False)
        df = self._parse_data(soup)
        return df

    def _parse_data(self, soup: BeautifulSoup) -> pd.DataFrame:
        """Parse data from the soup"""
        # the dashboard URL
        link = soup.find("iframe", {"title": "Covid Dashboard"})["src"]
        if not link:
            raise ValueError("Dashboard not found, please update the script")
        soup = get_soup(link, verify=False)
        # the metrics
        metrics = self._parse_metrics(soup)
        # DataFrame
        df = pd.DataFrame(
            {
                **metrics,
            }
        )
        return df

    def _parse_metrics(self, soup: BeautifulSoup) -> int:
        """Parse metrics from the soup"""
        total = soup.find(text=self.regex["Total"])
        dose2 = soup.find(text=self.regex["Dose2"])
        dose3 = soup.find(text=self.regex["Dose3"])
        boosters = soup.find(text=self.regex["Boosters"])
        if not total or not dose2 or not dose3 or not boosters:
            raise ValueError("Metrics not found, please update the script")
        total_vaccinations = clean_count(total.parent.find_next().text)
        people_fully_vaccinated = clean_count(dose2.parent.find_next().text)
        total_boosters = clean_count(dose3.parent.find_next().text) + clean_count(boosters.parent.find_next().text)
        people_vaccinated = total_vaccinations - people_fully_vaccinated - total_boosters
        df = {
            "people_vaccinated": [people_vaccinated],
            "people_fully_vaccinated": [people_fully_vaccinated],
            "total_boosters": [total_boosters],
            "total_vaccinations": [total_vaccinations],
        }
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes date"""
        return df.assign(date=localdate("Europe/Tirane"))

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipes vaccine names."""
        return df.assign(vaccine="Oxford/AstraZeneca, Pfizer/BioNTech")

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        """Pipeline for data processing"""
        return df.pipe(self.pipe_metadata).pipe(self.pipe_date).pipe(self.pipe_vaccine)

    def export(self):
        """Exports data to csv"""
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df, attach=True)


def main():
    Kosovo().export()

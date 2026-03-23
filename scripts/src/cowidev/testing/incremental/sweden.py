import re
from typing import Iterator
from datetime import timedelta

from epiweeks import Week
from bs4 import BeautifulSoup, element
import pandas as pd


from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_date, clean_count
from cowidev.testing import CountryTestBase


class Sweden(CountryTestBase):
    location = "Sweden"
    units = "tests performed"
    source_label = "Swedish Public Health Agency"
    notes = ""
    source_url = "https://www.folkhalsomyndigheten.se/smittskydd-beredskap/utbrott/aktuella-utbrott/covid-19/statistik-och-analyser/antalet-testade-for-covid-19/"
    regex = {
        "title": r"Antalet testade individer och genomförda test per",
        "week": r"[vV]ecka (\d+)",
    }

    def read(self) -> pd.DataFrame:
        """Reads data from source."""
        soup = get_soup(self.source_url)
        data = self._parse_data(soup)
        df = self._build_df(data)
        return df

    def _build_df(self, data: dict) -> pd.DataFrame:
        """Builds dataframe from data."""
        # Create dataframe
        df = pd.DataFrame([data])
        # Create date range (check week distance)
        dt_min = self._load_last_date() + timedelta(days=1)
        dt = clean_date(df.Date.max(), "%Y-%m-%d", as_datetime=True)
        if ((days_diff := (dt - dt_min).days) != 6) & (days_diff != -1):
            raise ValueError(f"Date distance is no longer a week ({days_diff})! Please check.")
        ds = pd.Series(pd.date_range(dt - timedelta(days=6), dt).astype(str), name="Date")
        # Distribute week value over 7 days
        df = df.merge(ds, how="right")
        df = df.assign(
            **{
                "Source URL": self.source_url,
                "Daily change in cumulative total": round(df["Daily change in cumulative total"].bfill()),
            }
        )
        return df

    def _parse_data(self, soup: BeautifulSoup) -> list:
        """Gets data from the source page."""
        # Extract the relevant element
        elem = self._get_relevant_element(soup)
        # Get the week number
        week_num = self._get_week_num_from_element(elem)
        # Extract the text from the element
        text = self._get_text_from_element(elem)
        # Extract the metrics
        weekly_change = self._parse_metrics(text, week_num)
        # Parse date
        date = self._parse_date(week_num)

        record = {
            "Date": date,
            "Daily change in cumulative total": round(weekly_change / 7),
        }
        return record

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.Tag:
        """Gets element from the soup."""
        elem_list = soup.find_all("h2")
        elem = [title for title in elem_list if self.regex["title"] in title.text]
        elem = elem[0]
        if not elem:
            raise TypeError("Website Structure Changed, please update the script")
        return elem

    def _get_week_num_from_element(self, elem: element.Tag) -> int:
        """Gets week number from element."""
        week_num = int(re.search(self.regex["week"], elem.text).group(1))
        if week_num == 1:
            raise ValueError("Week 1: New Year, please update date in the script")
        return week_num

    def _get_text_from_element(self, elem: element.Tag) -> str:
        """Gets text from element."""
        elem = elem.find_next_sibling("table").text.replace(" ", "").replace("\n", " ")
        return elem

    def _parse_metrics(self, text: str, week_num) -> int:
        """Gets metrics from the text."""
        count = re.search(fr"[vV]ecka{week_num} \d+ (\d+)", text).group(1)
        return clean_count(count)

    def _parse_date(self, week_num) -> Iterator:
        """parses the date from the week number."""
        date = Week(2022, week_num, system="iso").enddate()
        return clean_date(date)

    def _load_last_date(self) -> str:
        """Loads the last date from the datafile."""
        df_current = self.load_datafile()
        date = df_current.Date.max()
        return clean_date(date, "%Y-%m-%d", as_datetime=True)

    def export(self):
        """Exports data to csv."""
        df = self.read().pipe(self.pipe_metadata)
        self.export_datafile(df, attach=True)


def main():
    Sweden().export()

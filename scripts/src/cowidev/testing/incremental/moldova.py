import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, clean_date
from cowidev.testing.utils.incremental import increment


class Moldova:
    location = "Moldova"
    units = "tests performed"
    source_label = "Ministry of Health of the Republic of Moldova"
    notes = ""
    source_url = "https://msmps.gov.md/media/comunicate/"
    regex = {
        "title": r"(cazuri noi de COVID-19)|(cazuri de COVID-19)|(cazuri de COVID-19,)",
        "date": r"(\d+\/\d+\/\d+)",
        "count": r"((\d+)) teste.|(\d+) de teste",
    }
    # Initial value for cumulative total: 364317

    def read(self) -> pd.Series:
        """Read data from source."""
        soup = get_soup(self.source_url)
        data = self._parse_data(soup)
        return pd.Series(data)

    def _parse_data(self, soup: BeautifulSoup) -> tuple:
        """Get data from the source page."""
        # Get relevant element
        url = self._get_relevant_element(soup)
        # Extract URL from element
        # url = self._parse_link_from_element(elem)
        # Extract text from url
        text = self._get_text_from_url(url)
        # Extract date from text
        date = self._parse_date_from_text(text)
        # # Extract metrics from text
        daily_change = self._parse_metrics(text)
        record = {
            "source_url": url,
            "date": date,
            "daily_change": daily_change,
        }
        return record

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.Tag:
        """Get the relevant element in news feed."""

        for a in soup.find_all("a", class_="list__news_item-link font__bigger"):
            if "cazuri" in a.get("href"):
                link = a.get("href")
        if not link:
            raise ValueError("No data found, Please check the source.")
        return link

    def _get_text_from_url(self, url: str) -> str:
        """Extract text from the url."""
        text = get_soup(url).get_text()
        text = text.replace("-", "").replace(",", "")
        text = re.sub(r"(\d)\s(\d)", r"\1\2", text)
        return text

    def _parse_date_from_text(self, text: str) -> str:
        """Get date from text."""
        match = re.search(self.regex["date"], text)
        if not match:
            raise ValueError("No date found, Please check the source.")
        date = clean_date(match.group(1), "%d/%m/%Y", as_datetime=True) - pd.Timedelta(days=1)
        return str(date.date())

    # def _parse_link_from_element(self, elem: element.Tag) -> str:
    #     """Get link from relevant element."""
    #     link = elem.get("href")
    #     return link

    def _parse_metrics(self, text: str) -> int:
        """Get metrics from news text."""
        count = clean_count(re.search(self.regex["count"], text).group(0))
        return count

    def export(self):
        """Export data to CSV."""
        data = self.read()
        increment(
            sheet_name=self.location,
            country=self.location,
            units=self.units,
            date=data["date"],
            source_url=data["source_url"],
            source_label=self.source_label,
            daily_change=data["daily_change"],
            count=pd.NA,
        )


def main():
    Moldova().export()

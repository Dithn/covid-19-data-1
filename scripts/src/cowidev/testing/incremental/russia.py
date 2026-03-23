import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, clean_date
from cowidev.testing.utils.incremental import increment


class Russia:
    location = "Russia"
    units = "tests performed"
    source_label = "Government of the Russian Federation"
    notes = ""
    _base_url = "https://rospotrebnadzor.ru"
    _url_subdirectory = "/about/info/news/?PAGEN_1="
    _num_max_pages = 3
    regex = {
        "title": r"Информационный бюллетень о ситуации",
        "date": r"(\d+ \d+ \d+)",
        "count": r"проведено (\d+).* исследовани",
    }

    def read(self) -> pd.Series:
        data = []

        for cnt in range(1, self._num_max_pages + 1):
            url = f"{self._base_url}{self._url_subdirectory}{cnt}"
            soup = get_soup(url)
            data, proceed = self._parse_data(soup)
            if not proceed:
                break

        return pd.Series(data)

    def _parse_data(self, soup: BeautifulSoup) -> tuple:
        """Get data from the source page."""
        # Get relevant element
        elem = self._get_relevant_element(soup)
        if not elem:
            return None, True
        # Extract url from element
        url = self._get_link_from_element(elem)
        # Extract text from url
        text, date = self._get_text_and_date_from_url(url)
        count = self._parse_metrics(text)
        record = {
            "source_url": url,
            "date": date,
            "count": count,
        }
        return record, False

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.Tag:
        """Get the relevant element in news feed."""
        news_list = soup.find(class_="content").find(class_="page").find_all("a")

        url_idx = [i for i, news in enumerate(news_list) if self.regex["title"] in news.text]

        if not url_idx:
            return None
        return news_list[url_idx[0]]

    def _get_text_and_date_from_url(self, url: str) -> tuple:
        """Extract text from the url."""
        soup = get_soup(url)
        date = self._parse_date(soup)
        text = soup.find(class_="news-detail").text.replace("\n", " ").replace("\xa0", "")
        text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)
        return text, date

    def _parse_date(self, soup: BeautifulSoup) -> str:
        """Get date from relevant element."""
        date_text = soup.find(class_="date").text.replace(".", " ")
        date = re.search(self.regex["date"], date_text).group()
        return clean_date(date, "%d %m %Y")

    def _get_link_from_element(self, elem: element.Tag) -> str:
        """Get link from relevant element."""
        href = elem["href"]
        link = f"{self._base_url}{href}"
        return link

    def _parse_metrics(self, text: str) -> int:
        """Get metrics from news text."""
        count = int(re.search(self.regex["count"], text).group(1))
        return clean_count(count)

    def export(self):
        data = self.read()
        increment(
            sheet_name=self.location,
            country=self.location,
            units=self.units,
            date=data["date"],
            source_url=data["source_url"],
            source_label=self.source_label,
            count=data["count"],
        )


def main():
    Russia().export()

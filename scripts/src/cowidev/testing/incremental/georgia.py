import re

import json
from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, clean_date
from cowidev.testing.utils.incremental import increment


class Georgia:
    location = "Georgia"
    units = "tests performed"
    source_label = "Government of Georgia"
    notes = ""
    _base_url = "https://agenda.ge"
    _url_query_pt1 = "https://agenda.ge/ajax/get-nodes?pageOptions%5Btag%5D=&pageOptions%5Byear%5D=2022&pageOptions%5Btype%5D=news&pageOptions%5Blang%5D=en&listOptions%5Byear%5D=all&listOptions%5Bmonth%5D=0&listOptions%5Bday%5D=0&listOptions%5Bpage%5D="
    _url_query_pt2 = "&listOptions%5Bcount%5D=16&listOptions%5Brange%5D=all&listOptions%5Brows%5D=4&listOptions%5Bcolumns%5D=4&listOptions%5Brubric%5D=&listOptions%5Bcategory%5D="
    _num_max_pages = 3
    regex = {
        "title": r"(Georgia reports)|(coronavirus)",
        "date": r"(\d+ \w+ \d+)",
        "count": r"(\d+) tests .*? 24 hours",
    }

    def read(self) -> pd.Series:
        data = []

        for cnt in range(self._num_max_pages):
            url = f"{self._url_query_pt1}{cnt}{self._url_query_pt2}"
            jsn = json.loads(get_soup(url, "html.parser").text)
            soup = BeautifulSoup(jsn["result"], "html.parser")
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
        # Extract url and date from element
        url, date = self._get_link_and_date_from_element(elem)
        # Extract text from url
        text = self._get_text_from_url(url)
        daily_change = self._parse_metrics(text)
        record = {
            "source_url": url,
            "date": date,
            "daily_change": daily_change,
        }
        return record, False

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.Tag:
        """Get the relevant element in news feed."""
        news_list = soup.find_all("a", class_="node-teaser-title")
        url_idx = [
            i for i, news in enumerate(news_list) if re.search(self.regex["title"], news.text)
        ]

        if not url_idx:
            return None

        return news_list[url_idx[0]]

    def _get_text_from_url(self, url: str) -> str:
        """Extract text from the url."""
        soup = get_soup(url)
        text = soup.find("div", class_="row bodytext").get_text(strip=True).replace(",", "")
        return text

    def _get_link_and_date_from_element(self, elem: element.Tag) -> tuple:
        """Extract link and date from relevant element."""
        link = self._parse_link_from_element(elem)
        if not link:
            return None
        date = self._parse_date_from_element(elem)
        return link, date

    def _parse_date_from_element(self, elem: element.Tag) -> str:
        """Get date from relevant element."""
        date_tag = elem.findNextSibling("div", class_="node-teaser-time")
        date = re.search(self.regex["date"], date_tag.text).group()
        return clean_date(date, "%d %b %Y")

    def _parse_link_from_element(self, elem: element.Tag) -> str:
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
            daily_change=data["daily_change"],
        )


def main():
    Georgia().export()

import re

from bs4 import BeautifulSoup, element
import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean import clean_count, clean_date
from cowidev.vax.utils.incremental import increment, enrich_data


import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Iran:
    location = "Iran"
    _base_url = "https://irangov.ir/"
    _url_subdirectory = "ministry-of-health-and-medical-education"
    _num_max_pages = 3
    regex = {
        "title": r"Health Ministry's Updates on COVID-19",
        "date": r"(\d+\-\d+\-\d+)",
        "people_vaccinated": r"(\d+) Iranians have received the first dose",
        "people_fully_vaccinated": r"(\d+) people have so far received the second dose",
        "total_boosters": r"(\d+) people have received the third dose",
    }

    def read(self) -> pd.Series:
        data = []

        for cnt in range(1, self._num_max_pages + 1):
            url = f"{self._base_url}/{self._url_subdirectory}/{cnt}"
            soup = get_soup(url, verify=False)
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

        record = {
            "source_url": url,
            "date": date,
            **self._parse_metrics(text),
        }
        return record, False

    def _get_relevant_element(self, soup: BeautifulSoup) -> element.Tag:
        """Get the relevant element in news feed."""
        news_list = soup.find_all("h3")

        url_idx = [
            i for i, news in enumerate(news_list) if re.search(self.regex["title"], news.text)
        ]

        if not url_idx:
            return None
        return news_list[url_idx[0]]

    def _get_text_from_url(self, url: str) -> str:
        """Extract text from the url."""
        soup = get_soup(url, verify=False)
        text = (
            soup.find("div", class_="content_detail_body")
            .get_text(strip=True)
            .replace("\xa0", " ")
            .replace(",", "")
        )
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
        date_tag = elem.findPreviousSibling("div").find("span")
        date = re.search(self.regex["date"], date_tag.text).group()
        return clean_date(date, "%Y-%m-%d")

    def _parse_link_from_element(self, elem: element.Tag) -> str:
        """Get link from relevant element."""
        href = elem.findParent("a")["href"]
        link = f"{self._base_url}{href}"
        return link

    def _parse_metrics(self, text: str) -> dict:
        """Get metrics from news text."""
        people_vaccinated = int(re.search(self.regex["people_vaccinated"], text).group(1))
        people_fully_vaccinated = int(
            re.search(self.regex["people_fully_vaccinated"], text).group(1)
        )
        total_boosters = int(re.search(self.regex["total_boosters"], text).group(1))
        return {
            "people_vaccinated": clean_count(people_vaccinated),
            "people_fully_vaccinated": clean_count(people_fully_vaccinated),
            "total_boosters": clean_count(total_boosters),
            "total_vaccinations": clean_count(
                people_vaccinated + people_fully_vaccinated + total_boosters
            ),
        }

    def pipe_location(self, data_series: pd.Series) -> pd.Series:
        return enrich_data(data_series, "location", self.location)

    def pipe_vaccine(self, data_series: pd.Series) -> pd.Series:
        return enrich_data(
            data_series,
            "vaccine",
            "COVIran Barekat, Covaxin, FAKHRAVAC, Oxford/AstraZeneca, Razi Cov Pars, Sinopharm/Beijing, Soberana02, SpikoGen, Sputnik V",
        )

    def pipeline(self, data_series: pd.Series) -> pd.Series:
        return data_series.pipe(self.pipe_location).pipe(self.pipe_vaccine)

    def export(self):
        data = self.read().pipe(self.pipeline)
        increment(
            location=data["location"],
            total_vaccinations=data["total_vaccinations"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            total_boosters=data["total_boosters"],
            date=data["date"],
            source_url=data["source_url"],
            vaccine=data["vaccine"],
        )


def main():
    Iran().export()

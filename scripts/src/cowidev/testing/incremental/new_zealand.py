import pandas as pd

from cowidev.utils.web.scraping import get_soup, request_text
from cowidev.utils.clean import extract_clean_date
from cowidev.testing.utils.incremental import increment


class NewZealand:
    location = "New Zealand"
    units = "tests performed"
    source_label = "Ministry of Health"
    source_url = "https://www.health.govt.nz/our-work/diseases-and-conditions/covid-19-novel-coronavirus/covid-19-data-and-statistics/covid-19-testing-data"
    notes = ""

    def read(self):
        return {
            "count": self._parse_metric(),
            "date": self._parse_date(),
        }

    def _parse_metric(self):
        text = request_text(self.source_url, mode="raw")
        table = pd.read_html(text, index_col=0)[1]
        count = int(table.loc["All COVID-19 viral tests administered*"])
        return count

    def _parse_date(self):
        soup = get_soup(self.source_url)
        date_raw = soup.select_one(".pane-content .georgia-italic").text
        dt_raw = extract_clean_date(date_raw, regex="(\\d+ \\w+ 202\\d)", date_format="%d %B %Y")
        return dt_raw

    def export(self):
        data = self.read()
        increment(
            count=data["count"],
            sheet_name=self.location,
            country=self.location,
            units=self.units,
            date=data["date"],
            source_url=self.source_url,
            source_label=self.source_label,
        )


def main():
    NewZealand().export()

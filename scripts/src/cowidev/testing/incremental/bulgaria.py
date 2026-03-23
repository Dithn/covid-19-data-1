import pandas as pd

from cowidev.utils.web import get_soup
from cowidev.utils.clean.dates import localdate
from cowidev.testing.utils.incremental import increment


class Bulgaria:
    location: str = "Bulgaria"
    units: str = "tests performed"
    source_label: str = "Bulgaria COVID-10 Information Portal"
    source_url: str = "https://coronavirus.bg/bg/statistika"

    def _parse_data(self):
        soup = get_soup(self.source_url)
        return {
            "count": self._parse_count(soup),
            "date": localdate("Europe/Sofia"),
        }

    def _parse_count(self, soup):
        # Read all tables
        soup = get_soup(self.source_url)
        tables = pd.read_html(str(soup))
        columns = {"Тип", "Общо", "Нови"}
        for table in tables:
            if not columns.difference(table.columns) and "RT PCR" in table["Тип"].tolist():
                return table.loc[table["Тип"] == "Общо", "Общо"].item()
        raise ValueError(f"Table not found! It may have changed its format.")

    def export(self):
        data = self._parse_data()
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
    Bulgaria().export()

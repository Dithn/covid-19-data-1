import pandas as pd

from cowidev.utils import clean_count
from cowidev.utils.clean.dates import localdate
from cowidev.utils.web import request_json
from cowidev.testing.utils.incremental import increment


class FaeroeIslands:
    location: str = "Faeroe Islands"
    units: str = "people tested"
    source_label: str = "The Government of the Faeroe Islands"
    source_url: str = "https://corona.fo/json/stats"
    source_url_ref: str = "https://corona.fo/api"
    notes: str = ""

    def _parse_data(self) -> pd.Series:
        data = request_json(self.source_url)["stats"]
        data = pd.DataFrame.from_records(data, columns=["tested"]).iloc[0]
        return {
            "count": clean_count(data[0]),
            "date": localdate("Atlantic/Faeroe"),
        }

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
    FaeroeIslands().export()

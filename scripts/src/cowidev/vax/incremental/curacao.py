import pandas as pd

from cowidev.utils.clean.dates import localdate
from cowidev.utils.web import request_json
from cowidev.vax.utils.incremental import enrich_data, increment


class Curacao:
    location = "Curacao"
    source_url = "https://bakuna-counter.ibis-management.com/init/"
    source_url_ref = "https://bakuna.cw/"
    vaccine = "Pfizer/BioNTech, Moderna"

    def read(self) -> pd.Series:
        data = self._parse_data()
        return pd.Series(
            {
                "people_vaccinated": data["total.dosis1"],
                "people_fully_vaccinated": data["total.dosis2"],
                "total_boosters": data["total.booster"],
            }
        )

    def _parse_data(self) -> dict:
        data = request_json(self.source_url)
        return {d["code"]: d["count"] for d in data["stats"]}

    def pipe_total_vaccinations(self, ds: pd.Series) -> pd.Series:
        total_vaccinations = ds.people_vaccinated + ds.people_fully_vaccinated + ds.total_boosters
        return enrich_data(ds, "total_vaccinations", total_vaccinations)

    def pipe_date(self, ds: pd.Series) -> pd.Series:
        date_str = localdate("America/Curacao")
        return enrich_data(ds, "date", date_str)

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return ds.pipe(self.pipe_date).pipe(self.pipe_total_vaccinations)

    def export(self):
        data = self.read().pipe(self.pipeline)
        increment(
            location=self.location,
            total_vaccinations=data["total_vaccinations"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            total_boosters=data["total_boosters"],
            date=data["date"],
            source_url=self.source_url_ref,
            vaccine=self.vaccine,
        )


def main():
    Curacao().export()

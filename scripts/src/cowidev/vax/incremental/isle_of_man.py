import json

import requests
import pandas as pd

from cowidev.utils.clean.dates import localdate
from cowidev.vax.utils.incremental import enrich_data, increment
from cowidev.vax.utils.base import CountryVaxBase


class IsleOfMan(CountryVaxBase):
    location: str = "Isle of Man"
    source_url: str = (
        "https://wabi-west-europe-b-primary-api.analysis.windows.net/public/reports/querydata?synchronous=true"
    )
    source_url_ref: str = "https://covid19.gov.im/general-information/covid-19-vaccination-statistics/"
    metrics_mapping: dict = {
        "First dose": "people_vaccinated",
        "Second dose": "people_fully_vaccinated",
        "Booster dose": "total_boosters",
        "Third dose (NOT booster)": "third_dose",
    }

    def read(self) -> pd.Series:
        data = self.data_body
        df = json.loads(requests.post(self.source_url, headers=self.headers, data=data).content)["results"][0][
            "result"
        ]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"]
        return self._parse_data(df)

    @property
    def headers(Self):
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:85.0) Gecko/20100101 Firefox/85.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
            "X-PowerBI-ResourceKey": "a01ccc19-80ba-4458-9849-66d7e1e300b7",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://app.powerbi.com",
            "Referer": (
                "https://app.powerbi.com/view?r=eyJrIjoiYTAxY2NjMTktODBiYS00NDU4LTk4NDktNjZkN2UxZTMwMGI3IiwidCI6IjM"
                "5YzAwODM2LWVkMTItNDhkYS05Yjk3LTU5NGQ4MDhmMDNlNSIsImMiOjl9"
            ),
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

    @property
    def data_body(self):
        values = ["""[{{"Literal":{{"Value":"\'{}\'"}}}}]""".format(m) for m in self.metrics_mapping.keys()]
        values_2 = [
            """[{{\\"Literal\\":{{\\"Value\\":\\"\'{}\'\\"}}}}]""".format(m) for m in self.metrics_mapping.keys()
        ]
        data = '{"version":"1.0.0","queries":[{"Query":{"Commands":[{"SemanticQueryDataShapeCommand":{"Query":{"Version":2,"From":[{"Name":"m","Entity":"Medway","Type":0}],"Select":[{"Column":{"Expression":{"SourceRef":{"Source":"m"}},"Property":"Dose schedule"},"Name":"Medway.Dose schedule"},{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"m"}},"Property":"Date of vaccination"}},"Function":5},"Name":"CountNonNull(Medway.Date of vaccination)"}],"Where":[{"Condition":{"In":{"Expressions":[{"Column":{"Expression":{"SourceRef":{"Source":"m"}},"Property":"Dose schedule"}}],"Values":[__VALUES__]}}}],"OrderBy":[{"Direction":2,"Expression":{"Aggregation":{"Expression":{"Column":{"Expression":{"SourceRef":{"Source":"m"}},"Property":"Date of vaccination"}},"Function":5}}}]},"Binding":{"Primary":{"Groupings":[{"Projections":[0,1]}]},"DataReduction":{"DataVolume":4,"Primary":{"Window":{"Count":1000}}},"Version":1}}}]},"CacheKey":"{\\"Commands\\":[{\\"SemanticQueryDataShapeCommand\\":{\\"Query\\":{\\"Version\\":2,\\"From\\":[{\\"Name\\":\\"m\\",\\"Entity\\":\\"Medway\\",\\"Type\\":0}],\\"Select\\":[{\\"Column\\":{\\"Expression\\":{\\"SourceRef\\":{\\"Source\\":\\"m\\"}},\\"Property\\":\\"Dose schedule\\"},\\"Name\\":\\"Medway.Dose schedule\\"},{\\"Aggregation\\":{\\"Expression\\":{\\"Column\\":{\\"Expression\\":{\\"SourceRef\\":{\\"Source\\":\\"m\\"}},\\"Property\\":\\"Date of vaccination\\"}},\\"Function\\":5},\\"Name\\":\\"CountNonNull(Medway.Date of vaccination)\\"}],\\"Where\\":[{\\"Condition\\":{\\"In\\":{\\"Expressions\\":[{\\"Column\\":{\\"Expression\\":{\\"SourceRef\\":{\\"Source\\":\\"m\\"}},\\"Property\\":\\"Dose schedule\\"}}],\\"Values\\":[__VALUES2__]}}}],\\"OrderBy\\":[{\\"Direction\\":2,\\"Expression\\":{\\"Aggregation\\":{\\"Expression\\":{\\"Column\\":{\\"Expression\\":{\\"SourceRef\\":{\\"Source\\":\\"m\\"}},\\"Property\\":\\"Date of vaccination\\"}},\\"Function\\":5}}}]},\\"Binding\\":{\\"Primary\\":{\\"Groupings\\":[{\\"Projections\\":[0,1]}]},\\"DataReduction\\":{\\"DataVolume\\":4,\\"Primary\\":{\\"Window\\":{\\"Count\\":1000}}},\\"Version\\":1}}}]}","QueryId":"","ApplicationContext":{"DatasetId":"819a1554-706f-4e7e-9f7d-ec4bf4a353e2","Sources":[{"ReportId":"a1d3f3f4-2b99-4dda-82af-e751394400c5"}]}}],"cancelQueries":[],"modelId":1616759}'.replace(
            "__VALUES__", ",".join(values)
        ).replace(
            "__VALUES2__", ",".join(values_2)
        )
        return data

    def _parse_data(self, df: pd.DataFrame) -> pd.Series:
        data = {
            value: [elem["C"][1] for elem in df if elem["C"][0] == key][0]
            for key, value in self.metrics_mapping.items()
        }
        return pd.Series(data=data)

    def pipe_metrics(self, ds: pd.Series) -> pd.Series:
        ds["total_boosters"] += ds["third_dose"]
        ds = enrich_data(
            ds, "total_vaccinations", ds["people_vaccinated"] + ds["people_fully_vaccinated"] + ds["total_boosters"]
        )
        return ds

    def pipe_date(self, ds: pd.Series) -> pd.Series:
        date = localdate("Europe/Isle_of_Man")
        return enrich_data(ds, "date", date)

    def pipe_location(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "location", self.location)

    def pipe_vaccine(self, ds: pd.Series) -> pd.Series:
        return enrich_data(ds, "vaccine", "Moderna, Oxford/AstraZeneca, Pfizer/BioNTech")

    def pipe_source(self, ds: pd.Series) -> pd.Series:
        return enrich_data(
            ds,
            "source_url",
            self.source_url_ref,
        )

    def pipeline(self, ds: pd.Series) -> pd.Series:
        return (
            ds.pipe(self.pipe_metrics)
            .pipe(self.pipe_date)
            .pipe(self.pipe_location)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_source)
        )

    def export(self):
        data = self.read().pipe(self.pipeline)
        increment(
            location=self.location,
            total_vaccinations=data["total_vaccinations"],
            people_vaccinated=data["people_vaccinated"],
            people_fully_vaccinated=data["people_fully_vaccinated"],
            total_boosters=data["total_boosters"],
            date=data["date"],
            source_url=data["source_url"],
            vaccine=data["vaccine"],
        )
        self.force_monotonic()


def main():
    IsleOfMan().export()

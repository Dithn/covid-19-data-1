import pandas as pd

from cowidev.utils.utils import check_known_columns
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import build_vaccine_timeline


class Estonia(CountryVaxBase):
    location: str = "Estonia"
    source_url: str = "https://opendata.digilugu.ee/covid19/vaccination/v3/opendata_covid19_vaccination_total.csv"
    source_url_ref: str = "https://opendata.digilugu.ee"

    def read(self) -> pd.DataFrame:
        return self._parse_data()

    def _parse_metric(self, df, series, measurement, metric_name) -> pd.DataFrame:
        df = (
            df[(df.VaccinationSeries.isin(series)) & (df.MeasurementType == measurement)][
                ["StatisticsDate", "TotalCount"]
            ]
            .rename(columns={"StatisticsDate": "date", "TotalCount": metric_name})
            .groupby("date", as_index=False)
            .sum()
        )
        return df

    def _parse_data(self) -> pd.DataFrame:
        df = pd.read_csv(self.source_url)

        check_known_columns(
            df,
            [
                "StatisticsDate",
                "TargetDiseaseCode",
                "TargetDisease",
                "MeasurementType",
                "DailyCount",
                "TotalCount",
                "PopulationCoverage",
                "VaccinationSeries",
                "LocationPopulation",
            ],
        )

        total_vaccinations = self._parse_metric(
            df, series=range(1, 1000), measurement="DosesAdministered", metric_name="total_vaccinations"
        )
        people_vaccinated = self._parse_metric(
            df, series=[1], measurement="Vaccinated", metric_name="people_vaccinated"
        )
        people_fully_vaccinated = self._parse_metric(
            df, series=[1], measurement="FullyVaccinated", metric_name="people_fully_vaccinated"
        )
        total_boosters = self._parse_metric(
            df, series=range(2, 1000), measurement="DosesAdministered", metric_name="total_boosters"
        )

        df = (
            pd.merge(people_fully_vaccinated, people_vaccinated, on="date", how="outer", validate="one_to_one")
            .merge(total_vaccinations, on="date", how="outer", validate="one_to_one")
            .merge(total_boosters, on="date", how="outer", validate="one_to_one")
        )

        return df

    def pipe_location(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location)

    def pipe_vaccine_name(self, df: pd.DataFrame) -> pd.DataFrame:
        df = build_vaccine_timeline(
            df,
            {
                "Pfizer/BioNTech": "2020-12-01",
                "Moderna": "2021-01-14",
                "Oxford/AstraZeneca": "2021-02-09",
                "Johnson&Johnson": "2021-04-14",
                # Source: https://www.ecdc.europa.eu/en/publications-data/data-covid-19-vaccination-eu-eea
                "Novavax": "2022-03-04",
            },
        )
        return df

    def pipe_source(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(source_url=self.source_url_ref)

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_location).pipe(self.pipe_vaccine_name).pipe(self.pipe_source)

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Estonia().export()

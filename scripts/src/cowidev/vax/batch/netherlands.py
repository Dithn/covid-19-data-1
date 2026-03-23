import pandas as pd

from cowidev.utils.clean.dates import week_to_date
from cowidev.vax.utils.utils import build_vaccine_timeline
from cowidev.vax.utils.checks import VACCINES_ONE_DOSE
from cowidev.vax.utils.base import CountryVaxBase


class Netherlands(CountryVaxBase):
    source_url: str = (
        "https://github.com/mzelst/covid-19/raw/master/data-rivm/vaccines-ecdc/vaccines_administered_nl.csv"
    )
    source_url_ref = "https://github.com/mzelst/covid-19"
    location: str = "Netherlands"
    vax_timeline: dict = None
    vaccines_mapping: dict = {
        "Oxford/AstraZeneca": "Oxford/AstraZeneca",
        "Pfizer/BioNTech": "Pfizer/BioNTech",
        "Moderna": "Moderna",
        "Johnson&Johnson": "Johnson&Johnson",
        "NVXD": "Novavax",
    }

    def read(self):
        return pd.read_csv(self.source_url)

    def pipe_filter_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df[df.total_administered > 0]
        return df

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.assign(date=df.apply(lambda x: week_to_date(x.year, x.week), axis=1)).drop(columns=["week", "year"])
        return df

    def pipe_get_vax_timeline(self, df: pd.DataFrame) -> pd.DataFrame:
        df_ = df[df.vaccine != "UNK"]
        vax_wrong = set(df_.vaccine).difference(self.vaccines_mapping)
        if vax_wrong:
            raise ValueError(f"Some unknown vaccines were found {vax_wrong}")
        self.vax_timeline = df_[["vaccine", "date"]].groupby("vaccine").min().to_dict()["date"]
        self.vax_timeline = {self.vaccines_mapping[vax]: date for vax, date in self.vax_timeline.items()}
        # print(self.vax_timeline)
        return df

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        # Total vaccinations
        df["total_vaccinations"] = df.total_administered
        # People vaccinated
        df.loc[df.dose_number == 1, "people_vaccinated"] = df.total_administered
        # People fully vaccinated
        df.loc[
            (df.dose_number == 2) & (-df.vaccine.isin(VACCINES_ONE_DOSE)), "people_fully_vaccinated"
        ] = df.total_administered
        df.loc[
            (df.dose_number == 1) & (df.vaccine.isin(VACCINES_ONE_DOSE)), "people_fully_vaccinated"
        ] = df.total_administered
        # Boosters
        df.loc[(df.dose_number > 2) & (-df.vaccine.isin(VACCINES_ONE_DOSE)), "total_boosters"] = df.total_administered
        df.loc[(df.dose_number > 1) & (df.vaccine.isin(VACCINES_ONE_DOSE)), "total_boosters"] = df.total_administered
        return df

    def pipe_metrics_aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = (
            df.drop(columns=["dose_number", "total_administered", "vaccine"])
            .fillna(0)
            .groupby("date", as_index=False)
            .sum()
            .sort_values("date")
        )
        return df

    def pipe_metrics_cumsum(self, df: pd.DataFrame) -> pd.DataFrame:
        df[["people_vaccinated", "people_fully_vaccinated", "total_vaccinations", "total_boosters"]] = df[
            ["people_vaccinated", "people_fully_vaccinated", "total_vaccinations", "total_boosters"]
        ].cumsum()
        return df

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location, source_url=self.source_url_ref)

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        df = build_vaccine_timeline(df, self.vax_timeline)
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_filter_rows)
            .pipe(self.pipe_date)
            .pipe(self.pipe_get_vax_timeline)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_metrics_aggregate)
            .pipe(self.pipe_metrics_cumsum)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_vaccine)[
                [
                    "location",
                    "date",
                    "vaccine",
                    "source_url",
                    "total_vaccinations",
                    "people_vaccinated",
                    "people_fully_vaccinated",
                    "total_boosters",
                ]
            ]
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def main():
    Netherlands().export()

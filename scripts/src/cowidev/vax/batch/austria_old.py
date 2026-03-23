import pandas as pd

from cowidev.utils.utils import check_known_columns
from cowidev.utils.web.download import read_csv_from_url
from cowidev.vax.utils.base import CountryVaxBase


class Austria(CountryVaxBase):
    location: str = "Austria"
    source_url: str = "https://info.gesundheitsministerium.gv.at/data/COVID19_vaccination_doses_timeline_v202206.csv"    
    source_url_ref: str = "https://info.gesundheitsministerium.gv.at/opendata/"
    vaccine_mapping: dict = {
        "BioNTechPfizer": "Pfizer/BioNTech",
        "Moderna": "Moderna",
        "AstraZeneca": "Oxford/AstraZeneca",
        "Janssen": "Johnson&Johnson",
        "Novavax": "Novavax",
        "Valneva": "Valneva",
    }
    one_dose_vaccines: str = ["Janssen"]

    def read(self) -> pd.DataFrame:
        df = read_csv_from_url(self.source_url, sep=";", ciphers_low=True)
        check_known_columns(
            df, ["date", "state_id", "state_name", "vaccine", "dose_number", "doses_administered_cumulative"]
        )
        return df[["date", "state_name", "vaccine", "dose_number", "doses_administered_cumulative"]]

    def pipe_filter_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[(df["state_name"] == "Österreich") & (df.vaccine != "Other")].drop(columns="state_name")

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(date=df.date.str.slice(0, 10))

    def pipe_reshape(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pivot(
            index=["date", "vaccine"], columns="dose_number", values="doses_administered_cumulative"
        ).reset_index()

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        assert [*df.columns] == [
            "date",
            "vaccine",
            "1",
            "2",
            "3",
            "4",
            "5+",
        ], "Wrong list of columns! Maybe a nth dose was added?"

        # Total vaccinations
        df.loc[:, "total_vaccinations"] = df["1"] + df["2"] + df["3"] + df["4"] + df["5+"]

        # People vaccinated
        df.loc[:, "people_vaccinated"] = df["1"]

        # People fully vaccinated
        df.loc[df.vaccine.isin(self.one_dose_vaccines), "people_fully_vaccinated"] = df["1"]
        df.loc[-df.vaccine.isin(self.one_dose_vaccines), "people_fully_vaccinated"] = df["2"]

        # Total boosters
        df.loc[:, "total_boosters"] = df["3"] + df["4"] + df["5+"]
        df.loc[df.vaccine.isin(self.one_dose_vaccines), "total_boosters"] += df["2"]

        return (
            df[
                [
                    "date",
                    "people_vaccinated",
                    "people_fully_vaccinated",
                    "total_vaccinations",
                    "total_boosters",
                ]
            ]
            .groupby("date", as_index=False)
            .sum()
        )

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            location=self.location,
            source_url=self.source_url,
        )

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        def _make_list(date: str) -> str:
            vax_list = ["Pfizer/BioNTech"]
            if date >= "2021-01-15":
                vax_list.append("Moderna")
            if date >= "2021-02-08":
                vax_list.append("Oxford/AstraZeneca")
            if date >= "2021-03-15":
                vax_list.append("Johnson&Johnson")
            if date >= "2022-02-27":
                vax_list.append("Novavax")
            return ", ".join(sorted(vax_list))

        df["vaccine"] = df.date.apply(_make_list)
        return df

    def pipe_quick_fix(self, df: pd.DataFrame) -> pd.DataFrame:
        df.loc[df.people_fully_vaccinated > df.people_vaccinated, "people_fully_vaccinated"] = None
        return df

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_filter_rows)
            .pipe(self.pipe_check_vaccine)
            .pipe(self.pipe_date)
            .pipe(self.pipe_reshape)
            .pipe(self.pipe_metrics)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_quick_fix)
            .sort_values("date")
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df=df)


def main():
    Austria().export()

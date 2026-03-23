from cowidev.vax.utils.base import CountryVaxBase
import pandas as pd

from cowidev.utils.clean import clean_date_series
from cowidev.utils.utils import check_known_columns
from cowidev.vax.utils.utils import build_vaccine_timeline, make_monotonic


class Portugal(CountryVaxBase):
    location: str = "Portugal"
    source_url: str = "https://github.com/dssg-pt/covid19pt-data/raw/master/vacinas.csv"
    source_url_ref: str = "https://github.com/dssg-pt/covid19pt-data"
    columns_rename: dict = {
        "data": "date",
        "vacinas": "total_vaccinations",
        "pessoas_inoculadas": "people_vaccinated",
        "pessoas_vacinadas_completamente": "people_fully_vaccinated",
        "pessoas_reforço": "total_boosters",
    }

    def read(self) -> pd.DataFrame:
        df = pd.read_csv(self.source_url)
        check_known_columns(
            df,
            [
                "data",
                "doses",
                "doses_novas",
                "doses1",
                "doses1_novas",
                "doses2",
                "doses2_novas",
                "pessoas_vacinadas_completamente",
                "pessoas_vacinadas_completamente_novas",
                "pessoas_vacinadas_parcialmente",
                "pessoas_vacinadas_parcialmente_novas",
                "pessoas_inoculadas",
                "pessoas_inoculadas_novas",
                "vacinas",
                "vacinas_novas",
                "pessoas_vacinadas_completamente_continente",
                "pessoas_vacinadas_completamente_continente_novas",
                "pessoas_reforço",
                "pessoas_reforço_novas",
                "pessoas_reforço_continente",
                "pessoas_reforço_continente_novas",
                "pessoas_gripe",
                "pessoas_gripe_novas",
                "vacinas_reforço_e_gripe_novas",
                "reforço_80mais",
                "reforço_80mais_novas",
                "reforço_70_79",
                "reforço_70_79_novas",
                "reforço_65_69",
                "reforço_65_69_novas",
                "reforço_60_69",
                "reforço_60_69_novas",
                "reforço_50_59",
                "reforço_50_59_novas",
                "vacinação_iniciada_05_11",
                "vacinação_iniciada_05_11_novas",
                "pessoas_inoculadas_12mais",
                "reforço_40_49",
                "reforço_40_49_novas",
                "vacinação_completa_05_11_novas",
                "reforço_30_39_novas",
                "vacinação_completa_05_11",
                "reforço_18_29",
                "reforço_18_29_novas",
                "reforço_30_39",
            ],
        )
        return df[self.columns_rename.keys()]

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.columns_rename)

    def pipe_date(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(date=clean_date_series(df.date, format_input="%d-%m-%Y"))

    def pipe_vaccine(self, df: pd.DataFrame) -> pd.DataFrame:
        return build_vaccine_timeline(
            df,
            {
                "Pfizer/BioNTech": "2020-01-01",
                "Moderna": "2021-02-09",
                "Oxford/AstraZeneca": "2021-02-09",
                "Johnson&Johnson": "2021-04-26",
            },
        )

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(location=self.location, source_url=self.source_url_ref)

    def pipe_sanity_checks(self, df: pd.DataFrame) -> pd.DataFrame:
        assert all(df.total_vaccinations.fillna(0) >= df.people_vaccinated.fillna(0))
        return df

    def pipe_dropna(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.dropna(
            subset=["total_vaccinations", "people_vaccinated", "people_fully_vaccinated", "total_boosters"], how="all"
        )

    def pipe_columns_out(self, df: pd.DataFrame) -> pd.DataFrame:
        return df[
            [
                "date",
                "total_vaccinations",
                "people_vaccinated",
                "people_fully_vaccinated",
                "location",
                "source_url",
                "total_boosters",
                "vaccine",
            ]
        ]

    def _pipe_metrics(df: pd.DataFrame) -> pd.DataFrame:
        # Deprecated
        df = df.dropna(subset=["total_vaccinations"]).assign(
            people_vaccinated=df.pessoas_vacinadas_parcialmente + df.people_fully_vaccinated
        )
        return df[["date", "total_vaccinations", "people_vaccinated", "people_fully_vaccinated"]]

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(self.pipe_rename_columns)
            .pipe(self.pipe_date)
            .pipe(self.pipe_vaccine)
            .pipe(self.pipe_metadata)
            .pipe(self.pipe_dropna)
            .pipe(self.pipe_sanity_checks)
            .pipe(self.pipe_columns_out)
            .pipe(make_monotonic, max_removed_rows=20)
            .sort_values("date")
        )

    def export(self):
        df = self.read().pipe(self.pipeline)
        self.export_datafile(df)


def add_boosters(df: pd.DataFrame) -> pd.DataFrame:
    # Deprecated
    #
    # Booster data is only reported as rounded values in reports or press conference. No booster
    # data is available from the source as of Nov 26 2021, but Rui Barros from Publico is collecting
    # the data on GitHub.
    boosters = (
        pd.read_csv("https://raw.githubusercontent.com/ruimgbarros/vacinacao/master/booster_doses.csv")
        .rename(columns={"Data": "date", "n_doses_booster": "total_boosters"})
        .assign(location="Portugal")
    )
    boosters["date"] = boosters.date.str.slice(0, 10)
    df = pd.merge(df, boosters, how="outer", on=["date", "location"], validate="one_to_one").sort_values("date")
    df.loc[df.source_url.isna(), "source_url"] = "https://github.com/ruimgbarros/vacinacao"
    df["total_vaccinations"] = df.total_vaccinations + df.total_boosters.ffill().fillna(0)
    return df


def main():
    Portugal().export()

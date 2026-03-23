import pandas as pd

from cowidev.utils.utils import check_known_columns
from cowidev.vax.utils.base import CountryVaxBase
from cowidev.vax.utils.utils import build_vaccine_timeline

vaccine_mapping = {
    "Comirnaty": "Pfizer/BioNTech",
    "Comirnaty 6m-4": "Pfizer/BioNTech",
    "Comirnaty 5-11": "Pfizer/BioNTech",
    "Comirnaty Original/Omicron BA.1": "Pfizer/BioNTech",
    "Comirnaty Original/Omicron BA.4/BA.5": "Pfizer/BioNTech",
    "Comirnaty Omicron XBB.1.5.": "Pfizer/BioNTech",
    "Comirnaty Omicron XBB.1.5. 5-11": "Pfizer/BioNTech",
    "COMIRNATY OMICRON XBB.1.5 6m-4": "Pfizer/BioNTech",
    "SPIKEVAX": "Moderna",
    "Spikevax bivalent Original/Omicron BA.1": "Moderna",
    "SPIKEVAX BIVALENT ORIGINAL/OMICRON BA.4-5": "Moderna",
    "Covishield": "Oxford/AstraZeneca",
    "VAXZEVRIA": "Oxford/AstraZeneca",
    "COVID-19 Vaccine Janssen": "Johnson&Johnson",
    "Nuvaxovid": "Novavax",
    "Nuvaxovid XBB 1.5": "Novavax",
    "Covovax": "Novavax",
    "Sinopharm": "Sinopharm/Beijing",
    "Sinovac": "Sinovac",
    "COVAXIN": "Covaxin",
    "Sputnik V": "Sputnik V",
    "Valneva": "Valneva",
}
one_dose_vaccines = ["Johnson&Johnson"]


def read(source: str) -> pd.DataFrame:
    df = pd.read_csv(source)
    check_known_columns(
        df,
        [
            "id",
            "datum",
            "vakcina",
            "kraj_nuts_kod",
            "kraj_nazev",
            "vekova_skupina",
            "prvnich_davek",
            "druhych_davek",
            "celkem_davek",
        ],
    )
    return df


def check_vaccine_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["vakcina"])
    unknown_vaccines = set(df.vakcina.unique()).difference(set(vaccine_mapping.keys()))
    if unknown_vaccines:
        raise ValueError("Found unknown vaccines: {}".format(unknown_vaccines))
    return df


def translate_vaccine_names(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace(vaccine_mapping)


def enrich_source(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(source_url="https://onemocneni-aktualne.mzcr.cz/covid-19")


def enrich_location(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(location="Czechia")


def enrich_metadata(df: pd.DataFrame) -> pd.DataFrame:
    return df.pipe(enrich_location).pipe(enrich_source)


def base_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    return df.pipe(check_vaccine_names).pipe(translate_vaccine_names)


def breakdown_per_vaccine(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(by=["datum", "vakcina"], as_index=False)[["celkem_davek"]]
        .sum()
        .sort_values("datum")
        .assign(size=lambda df: df.groupby(by=["vakcina"], as_index=False)["celkem_davek"].cumsum())
        .drop("celkem_davek", axis=1)
        .rename(
            columns={
                "datum": "date",
                "vakcina": "vaccine",
                "size": "total_vaccinations",
            }
        )
        .pipe(enrich_location)
    )


def aggregate_by_date_vaccine(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.assign(boosters=df["celkem_davek"] - df["prvnich_davek"] - df["druhych_davek"])
        .groupby(by=["datum", "vakcina"])[["prvnich_davek", "druhych_davek", "boosters", "celkem_davek"]]
        .sum()
        .reset_index()
        .rename(
            {
                "prvnich_davek": 1,
                "druhych_davek": 2,
                "boosters": "total_boosters",
                "celkem_davek": "total_vaccinations",
            },
            axis=1,
        )
    )


def infer_one_dose_vaccines(df: pd.DataFrame) -> pd.DataFrame:
    df.loc[df.vakcina.isin(one_dose_vaccines), 2] = df[1]
    return df


def remove_vaccines(df: pd.DataFrame, vaccine_schedule: dict) -> dict:
    vax_amount = df[["vakcina", "total_vaccinations"]].groupby("vakcina").sum()
    vax_amount = vax_amount.where(lambda x: x < 100).dropna()
    for v in vax_amount.index:
        vaccine_schedule.pop(v, None)  # It has never been approved in Czechia
    return vaccine_schedule


def aggregate_by_date(df: pd.DataFrame) -> pd.DataFrame:
    vaccine_schedule = df[["datum", "vakcina"]].groupby("vakcina").min().to_dict()["datum"]
    vaccine_schedule = remove_vaccines(df, vaccine_schedule)
    return (
        df.groupby(by="datum")
        .agg(
            people_vaccinated=(1, "sum"),  # 1 means 1st dose
            people_fully_vaccinated=(2, "sum"),
            total_vaccinations=("total_vaccinations", "sum"),
            total_boosters=("total_boosters", "sum"),
        )
        .reset_index()
        .rename(columns={"datum": "date"})
        .pipe(build_vaccine_timeline, vaccine_schedule)
    )


def format_date(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(date=df.date.astype(str).str.slice(0, 10))


def enrich_cumulated_sums(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(by="date").assign(
        **{
            col: df[col].cumsum().astype(int)
            for col in [
                "total_vaccinations",
                "people_vaccinated",
                "people_fully_vaccinated",
                "total_boosters",
            ]
        }
    )


class Czechia(CountryVaxBase):
    location = "Czechia"
    source_url = "https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/ockovani.csv"

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.pipe(aggregate_by_date_vaccine)
            .pipe(infer_one_dose_vaccines)
            .pipe(aggregate_by_date)
            .pipe(format_date)
            .pipe(enrich_cumulated_sums)
            .pipe(enrich_metadata)
        )

    def export(self):
        base = read(self.source_url).pipe(base_pipeline)

        # Manufacturer data
        df_man = base.pipe(breakdown_per_vaccine)

        # Main data
        df = base.pipe(self.pipeline)
        self.export_datafile(
            df=df,
            df_manufacturer=df_man,
            meta_manufacturer={"source_name": "Ministry of Health", "source_url": self.source_url},
        )


def main():
    Czechia().export()

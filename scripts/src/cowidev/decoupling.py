import os
import sys

import pandas as pd
import requests

from cowidev import PATHS

CURRENT_DIR = os.path.dirname(__file__)
sys.path.append(CURRENT_DIR)


DATASET_NAME = "COVID-19 - Decoupling of metrics"
ZERO_DAY = "2020-01-01"

SOURCE_USA_C_D = "https://covid.cdc.gov/covid-data-tracker/COVIDData/getAjaxData?id=us_trend_by_USA"
SOURCE_USA_HOSP_ICU = "https://healthdata.gov/api/views/g62h-syeh/rows.csv?accessType=DOWNLOAD"

SOURCE_ESP = "https://cnecovid.isciii.es/covid19/resources/casos_hosp_uci_def_sexo_edad_provres.csv"

SOURCE_ISR = "https://github.com/dancarmoz/israel_moh_covid_dashboard_data/raw/master/hospitalized_and_infected.csv"

SOURCE_DEU_C_D = "https://media.githubusercontent.com/media/robert-koch-institut/SARS-CoV-2-Infektionen_in_Deutschland/main/Aktuell_Deutschland_SarsCov2_Infektionen.csv"
SOURCE_DEU_HOSP = "https://raw.githubusercontent.com/robert-koch-institut/COVID-19-Hospitalisierungen_in_Deutschland/master/Aktuell_Deutschland_COVID-19-Hospitalisierungen.csv"
SOURCE_DEU_ICU = "https://diviexchange.blob.core.windows.net/%24web/zeitreihe-deutschland.csv"


def adjust_x_and_y(
    df: pd.DataFrame,
    start_date: str,
    end_date: str,
    hosp_variable: str,
    icu_variable: str,
) -> pd.DataFrame:
    df = df[df.date >= start_date].copy()

    df_period = df[(df.date >= start_date) & (df.date <= end_date)].copy()
    case_peak_date = df_period.sort_values("confirmed_cases").date.values[-1]
    hosp_peak_date = df_period.sort_values(hosp_variable).date.values[-1]
    icu_peak_date = df_period.sort_values(icu_variable).date.values[-1]
    death_peak_date = df_period.sort_values("confirmed_deaths").date.values[-1]

    case_peak = df.loc[df.date == case_peak_date, "confirmed_cases"].values[0]
    hosp_peak = df.loc[df.date == hosp_peak_date, hosp_variable].values[0]
    icu_peak = df.loc[df.date == icu_peak_date, icu_variable].values[0]
    death_peak = df.loc[df.date == death_peak_date, "confirmed_deaths"].values[0]

    hosp_shift = (pd.to_datetime(hosp_peak_date) - pd.to_datetime(case_peak_date)).days
    icu_shift = (pd.to_datetime(icu_peak_date) - pd.to_datetime(case_peak_date)).days
    death_shift = (pd.to_datetime(death_peak_date) - pd.to_datetime(case_peak_date)).days

    df[hosp_variable] = df[hosp_variable].shift(-hosp_shift)
    df[icu_variable] = df[icu_variable].shift(-icu_shift)
    df["confirmed_deaths"] = df.confirmed_deaths.shift(-death_shift)

    df["confirmed_cases"] = (100 * df.confirmed_cases / case_peak).round(1)
    df[hosp_variable] = (100 * df[hosp_variable] / hosp_peak).round(1)
    df[icu_variable] = (100 * df[icu_variable] / icu_peak).round(1)
    df["confirmed_deaths"] = (100 * df.confirmed_deaths / death_peak).round(1)

    return df


def process_usa() -> pd.DataFrame:
    c_d = requests.get(SOURCE_USA_C_D).json()["us_trend_by_Geography"]
    c_d = pd.DataFrame.from_records(
        c_d,
        columns=[
            "seven_day_avg_new_cases",
            "seven_day_avg_new_deaths",
            "date",
        ],
    ).rename(
        columns={
            "seven_day_avg_new_cases": "confirmed_cases",
            "seven_day_avg_new_deaths": "confirmed_deaths",
        }
    )
    c_d["date"] = pd.to_datetime(c_d.date, dayfirst=False).dt.date.astype(str)

    hosp_icu = pd.read_csv(
        SOURCE_USA_HOSP_ICU,
        usecols=[
            "date",
            "staffed_icu_adult_patients_confirmed_covid",
            "previous_day_admission_adult_covid_confirmed",
            "previous_day_admission_pediatric_covid_confirmed",
        ],
    ).rename(columns={"staffed_icu_adult_patients_confirmed_covid": "icu_stock"})
    hosp_icu["date"] = pd.to_datetime(hosp_icu.date, format="%Y/%m/%d").dt.date.astype(str)
    hosp_icu = hosp_icu.dropna(subset=["date"]).sort_values("date")
    hosp_icu["hospital_flow"] = hosp_icu.previous_day_admission_adult_covid_confirmed.fillna(0).add(
        hosp_icu.previous_day_admission_pediatric_covid_confirmed.fillna(0)
    )
    hosp_icu = (
        hosp_icu.groupby("date", as_index=False)
        .sum()
        .drop(
            columns=[
                "previous_day_admission_adult_covid_confirmed",
                "previous_day_admission_pediatric_covid_confirmed",
            ]
        )
    )
    hosp_icu["hospital_flow"] = hosp_icu.hospital_flow.rolling(7).sum()

    df = pd.merge(c_d, hosp_icu).sort_values("date").head(-3).assign(Country="United States")
    df = adjust_x_and_y(
        df,
        start_date="2020-10-01",
        end_date="2021-03-01",
        hosp_variable="hospital_flow",
        icu_variable="icu_stock",
    )

    return df


def process_deu() -> pd.DataFrame:
    cases_deaths = (
        pd.read_csv(SOURCE_DEU_C_D, usecols=["Refdatum", "AnzahlFall", "AnzahlTodesfall"])
        .rename(
            columns={
                "Refdatum": "date",
                "AnzahlFall": "confirmed_cases",
                "AnzahlTodesfall": "confirmed_deaths",
            }
        )
        .groupby("date", as_index=False)
        .sum()
        .sort_values("date")
    )
    cases_deaths[["confirmed_cases", "confirmed_deaths"]] = (
        cases_deaths[["confirmed_cases", "confirmed_deaths"]].rolling(7).sum()
    )

    hosp_flow = pd.read_csv(
        SOURCE_DEU_HOSP,
        usecols=["Datum", "Bundesland", "Altersgruppe", "7T_Hospitalisierung_Faelle"],
    )
    hosp_flow = (
        hosp_flow[(hosp_flow.Bundesland == "Bundesgebiet") & (hosp_flow.Altersgruppe == "00+")]
        .drop(columns=["Bundesland", "Altersgruppe"])
        .rename(columns={"Datum": "date", "7T_Hospitalisierung_Faelle": "hospital_flow"})
        .groupby("date", as_index=False)
        .sum()
    )

    icu_stock = (
        pd.read_csv(SOURCE_DEU_ICU, usecols=["Datum", "Aktuelle_COVID_Faelle_ITS"])
        .rename(columns={"Datum": "date", "Aktuelle_COVID_Faelle_ITS": "icu_stock"})
        .groupby("date", as_index=False)
        .sum()
    )
    icu_stock["date"] = icu_stock.date.str.slice(0, 10)

    df = (
        pd.merge(cases_deaths, hosp_flow, on="date", how="outer", validate="one_to_one")
        .merge(icu_stock, on="date", how="outer", validate="one_to_one")
        .assign(Country="Germany")
        .sort_values("date")
        .head(-4)
    )
    df = adjust_x_and_y(
        df,
        start_date="2020-10-01",
        end_date="2021-02-15",
        hosp_variable="hospital_flow",
        icu_variable="icu_stock",
    )

    return df


def process_esp() -> pd.DataFrame:
    df = (
        pd.read_csv(SOURCE_ESP, usecols=["fecha", "num_casos", "num_hosp", "num_uci", "num_def"])
        .rename(
            columns={
                "fecha": "date",
                "num_def": "confirmed_deaths",
                "num_casos": "confirmed_cases",
                "num_hosp": "hospital_flow",
                "num_uci": "icu_flow",
            }
        )
        .groupby("date", as_index=False)
        .sum()
        .assign(Country="Spain")
        .sort_values("date")
        .head(-8)
    )

    df[["confirmed_cases", "confirmed_deaths", "hospital_flow", "icu_flow"]] = (
        df[["confirmed_cases", "confirmed_deaths", "hospital_flow", "icu_flow"]].rolling(7).sum()
    )

    df = adjust_x_and_y(
        df,
        start_date="2020-12-15",
        end_date="2021-03-01",
        hosp_variable="hospital_flow",
        icu_variable="icu_flow",
    )

    return df


def process_isr() -> pd.DataFrame:
    df = (
        pd.read_csv(
            SOURCE_ISR,
            usecols=[
                "Date",
                "New infected",
                "New serious",
                "New deaths",
                "Easy",
                "Medium",
                "Hard",
            ],
        )
        .rename(
            columns={
                "Date": "date",
                "New infected": "confirmed_cases",
                "New serious": "icu_flow",
                "New deaths": "confirmed_deaths",
            }
        )
        .sort_values("date")
        .assign(Country="Israel")
        .head(-1)
    )

    df["hospital_stock"] = df.Easy + df.Medium + df.Hard

    vars = ["confirmed_cases", "icu_flow", "confirmed_deaths"]
    df[vars] = df[vars].rolling(7).sum()

    df = adjust_x_and_y(
        df,
        start_date="2020-11-15",
        end_date="2021-04-01",
        hosp_variable="hospital_stock",
        icu_variable="icu_flow",
    )

    return df


def main():
    usa = process_usa()
    # germany = process_deu()
    spain = process_esp()
    israel = process_isr()
    df = pd.concat([usa, spain, israel], ignore_index=True).rename(columns={"date": "Year"})
    df["Year"] = (pd.to_datetime(df.Year) - pd.to_datetime(ZERO_DAY)).dt.days
    df = df[
        [
            "Country",
            "Year",
            "confirmed_cases",
            "hospital_flow",
            "hospital_stock",
            "icu_flow",
            "icu_stock",
            "confirmed_deaths",
        ]
    ]
    df.to_csv(os.path.join(PATHS.INTERNAL_GRAPHER_DIR, f"{DATASET_NAME}.csv"), index=False)


# if __name__ == "__main__":
    # main()

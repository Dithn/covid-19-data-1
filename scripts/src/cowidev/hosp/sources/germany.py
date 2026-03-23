import pandas as pd
import numpy as np

METADATA = {
    "source_url": {
        "icu": "https://diviexchange.blob.core.windows.net/%24web/zeitreihe-deutschland.csv",
        "hosp": "https://raw.githubusercontent.com/robert-koch-institut/COVID-19-Hospitalisierungen_in_Deutschland/master/Aktuell_Deutschland_COVID-19-Hospitalisierungen.csv",
    },
    "source_url_ref": "https://github.com/robert-koch-institut/COVID-19-Hospitalisierungen_in_Deutschland/",
    "source_name": "Robert Koch Institute",
    "entity": "Germany",
}


def main() -> pd.DataFrame:
    # Hospital admissions
    hosp_flow = pd.read_csv(
        METADATA["source_url"]["hosp"], usecols=["Datum", "Bundesland", "Altersgruppe", "7T_Hospitalisierung_Faelle"]
    )
    hosp_flow = (
        hosp_flow[(hosp_flow.Bundesland == "Bundesgebiet") & (hosp_flow.Altersgruppe == "00+")]
        .drop(columns=["Bundesland", "Altersgruppe"])
        .rename(columns={"Datum": "date"})
        .groupby("date", as_index=False)
        .sum()
    )

    # ICU admissions and patients
    icu = (
        pd.read_csv(
            METADATA["source_url"]["icu"], usecols=["Datum", "Aktuelle_COVID_Faelle_ITS", "faelle_covid_erstaufnahmen"]
        )
        .rename(columns={"Datum": "date"})
        .groupby("date", as_index=False)
        .sum()
        .sort_values("date")
    )
    icu["date"] = icu.date.str.slice(0, 10)
    icu.loc[icu.faelle_covid_erstaufnahmen == 0, "faelle_covid_erstaufnahmen"] = np.nan
    icu["faelle_covid_erstaufnahmen"] = icu.faelle_covid_erstaufnahmen.rolling(7).sum()

    # Merge
    df = (
        pd.merge(hosp_flow, icu, on="date", how="outer")
        .sort_values("date")
        .melt(id_vars="date", var_name="indicator")
        .dropna(subset=["value"])
    )
    df["indicator"] = df["indicator"].replace(
        {
            "Aktuelle_COVID_Faelle_ITS": "Daily ICU occupancy",
            "7T_Hospitalisierung_Faelle": "Weekly new hospital admissions",
            "faelle_covid_erstaufnahmen": "Weekly new ICU admissions",
        },
    )

    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()

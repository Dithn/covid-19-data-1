import pandas as pd

from cowidev.utils.clean import clean_date_series


METADATA = {
    "source_url": {
        "main": "https://github.com/pcm-dpc/COVID-19/raw/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv",
        "flow": "https://covid19.infn.it/iss/csv_part/iss_bydate_italia_ricoveri.csv",
    },
    "source_url_ref": "https://github.com/pcm-dpc/COVID-19, https://covid19.infn.it/iss/",
    "source_name": "Ministry of Health and Higher Institute of Health",
    "entity": "Italy",
}


def main() -> pd.DataFrame:
    hosp_flow = (
        pd.read_csv(METADATA["source_url"]["flow"], usecols=["data", "casi"])
        .rename(columns={"data": "date"})
        .sort_values("date")
        .head(-5)
    )
    hosp_flow["casi"] = hosp_flow.casi.rolling(7).sum()

    df = (
        pd.read_csv(
            METADATA["source_url"]["main"],
            usecols=["data", "totale_ospedalizzati", "terapia_intensiva", "ingressi_terapia_intensiva"],
        )
        .rename(columns={"data": "date"})
        .sort_values("date")
    )
    df["date"] = clean_date_series(df.date, "%Y-%m-%dT%H:%M:%S")
    df["ingressi_terapia_intensiva"] = df.ingressi_terapia_intensiva.rolling(7).sum()

    df = (
        pd.merge(hosp_flow, df, on="date", how="outer", validate="one_to_one")
        .melt("date", var_name="indicator")
        .dropna(subset=["value"])
        .assign(entity=METADATA["entity"])
    )
    df["indicator"] = df.indicator.replace(
        {
            "casi": "Weekly new hospital admissions",
            "ingressi_terapia_intensiva": "Weekly new ICU admissions",
            "totale_ospedalizzati": "Daily hospital occupancy",
            "terapia_intensiva": "Daily ICU occupancy",
        }
    )

    return df, METADATA


if __name__ == "__main__":
    main()

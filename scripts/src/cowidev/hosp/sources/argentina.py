import pandas as pd

from cowidev.utils.clean import clean_date_series

METADATA = {
    "source_url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQfx9cCSShyDY5nFvORXRG9xIPzB7uTpLqRjx_CwLO2bj-5eK9B_a60kBDlSGhCDIEu6BXmkFHdKCZE/pub?gid=0&single=true&output=csv",
    "source_url_ref": "https://www.argentina.gob.ar/coronavirus/informes-diarios/reportes",
    "source_name": "Government of Argentina, via Rodrigo Maidana",
    "entity": "Argentina",
}


def main() -> pd.DataFrame:
    df = pd.read_csv(METADATA["source_url"], usecols=["Fecha", "Total UTI"])

    df = (
        df.assign(Fecha=clean_date_series(df.Fecha, "%d/%m/%Y"))
        .rename(columns={"Fecha": "date"})
        .melt("date", var_name="indicator")
    )

    df["indicator"] = df.indicator.replace({"Total UTI": "Daily ICU occupancy"})
    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()

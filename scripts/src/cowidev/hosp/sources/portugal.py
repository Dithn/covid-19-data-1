import requests

import pandas as pd
from cowidev.utils.clean import clean_date_series

METADATA = {
    "source_url": "https://github.com/dssg-pt/covid19pt-data/raw/master/data.csv",
    "source_url_ref": "https://github.com/dssg-pt/covid19pt-data",
    "source_name": "General Directorate of Health, via Data Science for Social Good Portugal",
    "entity": "Portugal",
}


def main() -> pd.DataFrame:
    df = pd.read_csv(METADATA["source_url"], usecols=["data", "internados", "internados_uci"]).rename(
        columns={"data": "date"}
    )

    df["date"] = clean_date_series(df.date, "%d-%m-%Y")
    df = df.melt("date", var_name="indicator").dropna(subset=["value"])
    df["indicator"] = df.indicator.replace(
        {
            "internados": "Daily hospital occupancy",
            "internados_uci": "Daily ICU occupancy",
        }
    )

    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()

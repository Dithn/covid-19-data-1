"""NOTE: No longer valid URL"""
import os
import tempfile

import pandas as pd

from cowidev.utils.clean import clean_date_series
from cowidev.utils.io import extract_zip


METADATA = {
    "source_url": "https://covid19-dashboard.ages.at/data/data.zip",
    "source_url_ref": "https://covid19-dashboard.ages.at/",
    "source_name": "Austrian Agency for Health and Food Safety",
    "entity": "Austria",
}


def read() -> pd.DataFrame:
    with tempfile.TemporaryDirectory() as tf:
        extract_zip(METADATA["source_url"], tf, verify=False, ciphers_low=True)
        df = pd.read_csv(
            os.path.join(tf, "CovidFallzahlen.csv"),
            sep=";",
            usecols=["Meldedat", "Bundesland", "FZHosp", "FZICU"],
        )
    return df


def main() -> pd.DataFrame:
    df = read()

    df = df[df.Bundesland == "Alle"].drop(columns="Bundesland").rename(columns={"Meldedat": "date"})
    df["date"] = clean_date_series(df.date, "%d.%m.%Y")

    # FZHosp only includes patients in a "normal ward", i.e. all patients – ICU patients
    df["FZHosp"] = df.FZHosp + df.FZICU

    df = df.melt("date", var_name="indicator").dropna(subset=["value"])
    df["indicator"] = df.indicator.replace(
        {
            "FZHosp": "Daily hospital occupancy",
            "FZICU": "Daily ICU occupancy",
        },
    )

    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()

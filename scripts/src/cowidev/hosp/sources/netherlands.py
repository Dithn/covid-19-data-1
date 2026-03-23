import pandas as pd

from cowidev.utils.clean import clean_date_series
from cowidev.utils.web.download import read_csv_from_url


METADATA = {
    # to be changed to https://lcps.nu/wp-content/uploads/covid-19-datafeed.csv
    "source_url": "https://lcps.nu/wp-content/uploads/covid-19-datafeed.csv",
    "source_url_ref": "https://lcps.nu/datafeed/",
    "source_name": "National Coordination Center Patient Distribution",
    "entity": "Netherlands",
}


def main() -> pd.DataFrame:
    df = pd.read_csv(
        METADATA["source_url"],
        usecols=[
            "datum",
            "kliniek_bezetting_covid",
            "kliniek_opnames_covid",
            "IC_bezetting_covid",
            "IC_opnames_covid",
        ],
    )
    df["datum"] = clean_date_series(df["datum"], "%d-%m-%Y")
    df = df.rename(columns={"datum": "date"}).sort_values("date")

    df["kliniek_opnames_covid"] = df["kliniek_opnames_covid"].rolling(7).sum()
    df["IC_opnames_covid"] = df.IC_opnames_covid.rolling(7).sum()

    df = df.melt("date", var_name="indicator").dropna(subset=["value"])
    df["indicator"] = df.indicator.replace(
        {
            "kliniek_bezetting_covid": "Daily hospital occupancy",
            "IC_bezetting_covid": "Daily ICU occupancy",
            "kliniek_opnames_covid": "Weekly new hospital admissions",
            "IC_opnames_covid": "Weekly new ICU admissions",
        }
    )

    df["entity"] = METADATA["entity"]

    df = df.drop_duplicates(["date", "indicator"], keep=False)

    return df, METADATA


if __name__ == "__main__":
    main()

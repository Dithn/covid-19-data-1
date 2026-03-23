import pandas as pd

METADATA = {
    "source_url": "https://epistat.sciensano.be/Data/COVID19BE_HOSP.csv",
    "source_url_ref": "https://epistat.sciensano.be/",
    "source_name": "Sciensano",
    "entity": "Belgium",
}


def main() -> pd.DataFrame:
    df = pd.read_csv(METADATA["source_url"], usecols=["DATE", "TOTAL_IN", "TOTAL_IN_ICU", "NEW_IN"])

    df = df.rename(columns={"DATE": "date"}).groupby("date", as_index=False).sum().sort_values("date")

    df["NEW_IN"] = df.NEW_IN.rolling(7).sum()

    df = df.melt("date", var_name="indicator").dropna(subset=["value"])
    df["indicator"] = df.indicator.replace(
        {
            "TOTAL_IN": "Daily hospital occupancy",
            "TOTAL_IN_ICU": "Daily ICU occupancy",
            "NEW_IN": "Weekly new hospital admissions",
        }
    )

    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()

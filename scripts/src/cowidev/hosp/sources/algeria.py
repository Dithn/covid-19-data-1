import pandas as pd


METADATA = {
    "source_url": (
        "https://raw.githubusercontent.com/yasserkaddour/covid19-icu-data-algeria/main/algeria-covid19-icu-data.csv"
    ),
    "source_url_ref": "https://github.com/yasserkaddour/covid19-icu-data-algeria/",
    "source_name": "Ministry of Health via github.com/yasserkaddour/covid19-icu-data-algeria/",
    "entity": "Algeria",
}


def main():
    df = pd.read_csv(METADATA["source_url"], usecols=["date", "in_icu"])
    df = df.melt("date", ["in_icu"], "indicator")
    df = df.assign(
        indicator=df.indicator.replace({"in_icu": "Daily ICU occupancy"}),
        entity=METADATA["entity"],
    )
    return df, METADATA


if __name__ == "__main__":
    main()

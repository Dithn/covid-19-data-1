import pandas as pd

METADATA = {
    "source_url": "https://raw.githubusercontent.com/fqj1994/covid-19-dataflow-jp/main/data/mhlw_hospitalization.csv",
    "source_url_ref": "https://www.mhlw.go.jp/stf/seisakunitsuite/newpage_00023.html",
    "source_name": "Ministry of Health, Labour and Welfare",
    "entity": "Japan",
}


def main():
    df = pd.read_csv(METADATA["source_url"])

    df = df.melt("date", var_name="indicator", value_vars=["hospitalized", "require_ventilator_or_in_icu"]).dropna()
    df["indicator"] = df.indicator.replace(
        {
            "hospitalized": "Daily hospital occupancy",
            "require_ventilator_or_in_icu": "Daily ICU occupancy",
        }
    )

    # Drop outliers
    df = df[~df["date"].isin(["2023-02-08"])]

    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()

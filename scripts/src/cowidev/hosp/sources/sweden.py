import pandas as pd
from cowidev.utils.web.download import read_csv_from_url

METADATA = {
    "source_url_ref": "https://www.socialstyrelsen.se/statistik-och-data/statistik/statistik-om-covid-19/",
    "source_name": "The Swedish National Board of Health and Welfare",
    "entity": "Sweden",
}

URL_HOSP = "https://static.dwcdn.net/data/oedm6.csv"
URL_ICU = "https://static.dwcdn.net/data/16JTc.csv"


def main() -> pd.DataFrame:
    # Load hospitalization data
    df_hosp = read_csv_from_url(URL_HOSP).rename(
        columns={
            "ReportDate": "date",
            "Uppskattad total": "Daily hospital occupancy",
        }
    )
    df_icu = read_csv_from_url(URL_ICU).rename(
        columns={
            "ReportDate": "date",
            "Uppskattad total": "Daily ICU occupancy",
        }
    )
    # Merge data from both sources and keep relevant columns
    df = pd.merge(df_hosp, df_icu, on="date", how="outer", validate="one_to_one")
    df = df[["date", "Daily hospital occupancy", "Daily ICU occupancy"]]
    # Melt dataframe into long format
    df = df.melt("date", var_name="indicator").dropna(subset=["value"])
    # Assign entity name
    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()

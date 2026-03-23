import requests

import pandas as pd

from epiweeks import Week


METADATA = {
    "source_url_flow": "https://data.gov.sg/api/action/package_show?id=covid-19-hospital-admissions",
    "source_url_ref": "https://covidsitrep.moh.gov.sg/; https://data.gov.sg/dataset/covid-19-hospital-admissions",
    "source_name": "Ministry of Health",
    "entity": "Singapore",
}

"https://beta.data.gov.sg/datasets/d_98e8d8ba612a748413c439550c3c6942/view"


def get_data() -> pd.DataFrame:
    # Get data
    base_url = "https://data.gov.sg/api/action/datastore_search"
    url = base_url + "?resource_id=d_98e8d8ba612a748413c439550c3c6942&limit=1000"
    response = requests.get(url)
    data = response.json()

    if ("result" not in data) | ("records" not in data["result"]):
        raise Exception("Couldn't retrieve data")

    df = pd.DataFrame.from_records(data["result"]["records"])

    return df


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    COLUMNS_RENAME = {
        "epi_week": "date",
        "new_admisison_type": "indicator",
        "count": "value",
    }
    # Keep relevant columns
    df = df[list(COLUMNS_RENAME.keys())]

    # Rename columns
    df = df.rename(columns=COLUMNS_RENAME)

    # Parse date
    df["date"] = df["date"].apply(lambda x: Week.fromstring(x).startdate()).astype("string")

    # Rename indicator values
    df["indicator"] = df.indicator.replace(
        {
            "Hospitalised": "Weekly new hospital admissions",
            "ICU": "Weekly new ICU admissions",
        }
    )

    # Add entity
    df["entity"] = METADATA["entity"]

    # Sort
    df = df.sort_values(["indicator", "date"])
    return df


def main():
    # Get data
    df = get_data()

    # Process data
    df = process_data(df)

    return df, METADATA


if __name__ == "__main__":
    main()

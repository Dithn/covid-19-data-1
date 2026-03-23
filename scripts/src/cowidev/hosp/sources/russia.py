import json

import pandas as pd

from cowidev.utils.clean import clean_date_series
from cowidev.utils.web import get_soup


METADATA = {
    "source_url_ref": "https://стопкоронавирус.рф/information/",
    "source_name": "Government of Russia",
    "entity": "Russia",
}


def main():

    soup = get_soup(METADATA["source_url_ref"])
    records = json.loads(soup.find("cv-stats-virus")[":charts-data"])

    df = (
        pd.DataFrame.from_records(records, columns=["date", "hospitalized"])
        .rename(columns={"hospitalized": "value"})
        .assign(entity=METADATA["entity"], indicator="Weekly new hospital admissions")
    )
    df["date"] = clean_date_series(df.date, "%d.%m.%Y")
    df = df[df.value > 0].sort_values("date")
    df["value"] = df.value.rolling(7).sum()
    df = df.dropna(subset=["value"])

    return df, METADATA


if __name__ == "__main__":
    main()

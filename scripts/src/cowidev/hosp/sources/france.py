import pandas as pd
from cowidev.utils.web.download import read_csv_from_url

METADATA = {
    "source_url": {
        "stock": "https://www.data.gouv.fr/fr/datasets/r/63352e38-d353-4b54-bfd1-f1b3ee1cabd7",
        "flow": "https://www.data.gouv.fr/fr/datasets/r/6fadff46-9efd-4c53-942a-54aca783c30c",
    },
    "source_url_ref": "https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/",
    "source_name": "Santé publique France",
    "entity": "France",
}


def main() -> pd.DataFrame:
    # Hospital & ICU patients
    stock = read_csv_from_url(METADATA["source_url"]["stock"], usecols=["sexe", "jour", "hosp", "rea"], sep=";")
    stock = (
        stock[stock.sexe == 0]
        .drop(columns=["sexe"])
        .rename(columns={"jour": "date"})
        .groupby("date", as_index=False)
        .sum()
    )

    # Hospital & ICU admissions
    flow = read_csv_from_url(METADATA["source_url"]["flow"], usecols=["jour", "incid_hosp", "incid_rea"], sep=";")
    flow = flow.rename(columns={"jour": "date"}).groupby("date", as_index=False).sum().sort_values("date")
    flow["incid_hosp"] = flow.incid_hosp.rolling(7).sum()
    flow["incid_rea"] = flow.incid_rea.rolling(7).sum()

    # Merge
    df = pd.merge(stock, flow, on="date", how="outer").melt("date", var_name="indicator").dropna(subset=["value"])
    df["indicator"] = df.indicator.replace(
        {
            "rea": "Daily ICU occupancy",
            "hosp": "Daily hospital occupancy",
            "incid_hosp": "Weekly new hospital admissions",
            "incid_rea": "Weekly new ICU admissions",
        },
    )

    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()

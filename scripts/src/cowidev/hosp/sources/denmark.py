import io
import os
import requests
import tempfile
import zipfile

import pandas as pd

from cowidev.utils.web.scraping import get_soup

METADATA = {
    "source_url_hosp": "https://covid19.ssi.dk/overvagningsdata/download-fil-med-overvaagningdata",
    "source_url_icu": "https://github.com/mok0/covid19-data-denmark/raw/master/covid19-data-denmark.csv",
    "source_url_ref": "https://covid19.ssi.dk/overvagningsdata/download-fil-med-overvaagningdata, https://github.com/mok0/covid19-data-denmark",
    "source_name": "Statens Serum Institut, covid19-data-denmark on GitHub",
    "entity": "Denmark",
}


def read() -> pd.DataFrame:
    soup = get_soup(METADATA["source_url_hosp"])
    zip_url = soup.find("accordions").find("a").get("href")

    with tempfile.TemporaryDirectory() as tf:
        r = requests.get(zip_url)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(tf)
        flow = pd.read_csv(
            os.path.join(tf, "Regionalt_DB", "06_nye_indlaeggelser_pr_region_pr_dag.csv"),
            encoding="ISO 8859-1",
            sep=";",
            usecols=["Dato", "Indlæggelser"],
        )
        stock = pd.read_csv(
            os.path.join(tf, "Regionalt_DB", "15_indlagte_pr_region_pr_dag.csv"),
            encoding="ISO 8859-1",
            sep=";",
            usecols=["Dato", "Indlagte"],
        )
    return flow, stock


def main() -> pd.DataFrame:
    flow, stock = read()

    flow = flow.rename(columns={"Dato": "date"}).groupby("date", as_index=False).sum().sort_values("date").head(-1)
    flow["Indlæggelser"] = flow.Indlæggelser.rolling(7).sum()

    stock = stock.rename(columns={"Dato": "date"}).groupby("date", as_index=False).sum()

    df = pd.merge(flow, stock, how="outer", on="date", validate="one_to_one")

    icu = pd.read_csv(METADATA["source_url_icu"], usecols=["date", "icu_now"])
    df = pd.merge(df, icu, on="date", how="outer", validate="one_to_one")

    df = df.melt("date", var_name="indicator").dropna(subset=["value"]).sort_values(["indicator", "date"])
    df["indicator"] = df.indicator.replace(
        {
            "Indlæggelser": "Weekly new hospital admissions",
            "Indlagte": "Daily hospital occupancy",
            "icu_now": "Daily ICU occupancy",
        },
    )

    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()

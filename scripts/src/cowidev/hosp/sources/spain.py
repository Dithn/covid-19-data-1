import pandas as pd

from cowidev.utils.web.scraping import get_soup
from cowidev.utils.clean import clean_date_series

METADATA = {
    "source_url": "",
    "source_url_ref": (
        "https://www.sanidad.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov/capacidadAsistencial.htm"
    ),
    "source_name": "Ministry of Health, Consumption and Social Welfare",
    "entity": "Spain",
}


def main() -> pd.DataFrame:
    soup = get_soup(METADATA["source_url_ref"])
    url = soup.find(class_="informacion").find("a")["href"]
    url = "https://www.sanidad.gob.es/profesionales/saludPublica/ccayes/alertasActual/nCov/" + url
    df = pd.read_csv(
        url,
        usecols=["Fecha", "Unidad", "OCUPADAS_COVID19", "INGRESOS_COVID19", "Provincia", "CCAA"],
        encoding="Latin-1",
        sep=",",
    )

    df["Fecha"] = clean_date_series(df.Fecha, "%m/%d/%Y", errors="coerce")
    df = (
        df.dropna(subset=["Fecha"])
        .drop_duplicates(subset=["Fecha", "Unidad", "Provincia", "CCAA"], keep="first")
        .dropna(subset=["Unidad"])
    )
    df.loc[df.Unidad.str.contains("U. Críticas"), "Unidad"] = "ICU"

    df = (
        df.drop(columns=["Provincia", "CCAA"])
        .groupby(["Fecha", "Unidad"], as_index=False)
        .sum()
        .sort_values("Unidad")
        .pivot(index="Fecha", columns="Unidad")
        .reset_index()
        .sort_values("Fecha")
    )
    df.columns = ["date", "hosp_stock", "icu_stock", "hosp_flow", "icu_flow"]

    df["hosp_flow"] = df.hosp_flow.rolling(7).sum()
    df["icu_flow"] = df.icu_flow.rolling(7).sum()

    df = df.melt("date", var_name="indicator").dropna(subset=["value"])
    df["indicator"] = df.indicator.replace(
        {
            "hosp_flow": "Weekly new hospital admissions",
            "icu_flow": "Weekly new ICU admissions",
            "hosp_stock": "Daily hospital occupancy",
            "icu_stock": "Daily ICU occupancy",
        }
    )

    df["entity"] = METADATA["entity"]

    return df, METADATA


if __name__ == "__main__":
    main()

import pandas as pd

METADATA = {
    "source_url": {
        "icu_stock": "https://github.com/MinCiencia/Datos-COVID19/raw/master/output/producto8/UCI_std.csv",
        "icu_flow": "https://github.com/MinCiencia/Datos-COVID19/raw/master/output/producto91/Ingresos_UCI_std.csv",
        "hosp_flow": "https://github.com/MinCiencia/Datos-COVID19/raw/master/output/producto92/Ingresos_Hospital_std.csv",
    },
    "source_url_ref": "https://github.com/MinCiencia/Datos-COVID19",
    "source_name": "Ministry of Health, via Ministry of Science GitHub repository",
    "entity": "Chile",
}


def main():

    icu_stock = (
        pd.read_csv(METADATA["source_url"]["icu_stock"], usecols=["fecha", "numero"])
        .rename(columns={"fecha": "date", "numero": "icu_stock"})
        .groupby("date", as_index=False)
        .sum()
    )

    icu_flow = pd.read_csv(METADATA["source_url"]["icu_flow"], usecols=["Fecha", "Casos"]).rename(
        columns={"Fecha": "date", "Casos": "icu_flow"}
    )
    icu_flow["icu_flow"] = icu_flow.icu_flow.mul(7).round()

    hosp_flow = pd.read_csv(METADATA["source_url"]["hosp_flow"], usecols=["Fecha", "Casos"]).rename(
        columns={"Fecha": "date", "Casos": "hosp_flow"}
    )
    hosp_flow["hosp_flow"] = hosp_flow.hosp_flow.mul(7).round()

    df = (
        pd.merge(icu_stock, icu_flow, on="date", how="outer", validate="one_to_one")
        .merge(hosp_flow, on="date", how="outer", validate="one_to_one")
        .melt(id_vars="date", var_name="indicator")
        .assign(entity=METADATA["entity"])
    )

    df.loc[:, "indicator"] = df.indicator.replace(
        {
            "icu_stock": "Daily ICU occupancy",
            "hosp_flow": "Weekly new hospital admissions",
            "icu_flow": "Weekly new ICU admissions",
        }
    )

    return df, METADATA


if __name__ == "__main__":
    main()

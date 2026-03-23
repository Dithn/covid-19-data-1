import numpy as np
import pandas as pd

METADATA = {
    "source_url": "https://github.com/sociedatos/bo-hospitalizados_por_departamento/raw/master/hospitalizados_por_departamento.csv",
    "source_url_ref": "https://github.com/sociedatos/bo-hospitalizados_por_departamento",
    "source_name": "Ministry of Health, via Sociedatos on GitHub",
    "entity": "Bolivia",
}


def main() -> pd.DataFrame:

    data = pd.read_csv(METADATA["source_url"])

    stock_cols = list(data.columns[data.iloc[0] == "hospitalizados"].values)
    keep_cols = ["Unnamed: 0"] + stock_cols
    df = data[keep_cols]

    df.columns = df.iloc[1].values
    df = df.rename(columns={np.nan: "date"}).iloc[3:].melt(id_vars="date", var_name="ward")
    df["value"] = df.value.astype(int)

    hosp_stock = (
        df.drop(columns="ward").groupby("date", as_index=False).sum().assign(indicator="Daily hospital occupancy")
    )

    icu_stock = (
        df[df.ward == "uci"]
        .drop(columns="ward")
        .groupby("date", as_index=False)
        .sum()
        .assign(indicator="Daily ICU occupancy")
    )

    df = pd.concat([hosp_stock, icu_stock], ignore_index=True).assign(entity=METADATA["entity"])

    return df, METADATA


if __name__ == "__main__":
    main()

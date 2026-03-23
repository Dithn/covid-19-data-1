"merge"
import pandas as pd


def get_cgrt(bsg_latest: str, bsg_diff_latest: str, country_mapping: str):
    """
    Downloads the latest OxCGRT dataset from BSG's GitHub repository
    Remaps BSG country names to OWID country names

    Returns:
        cgrt {dataframe}
    """
    country_mapping = pd.read_csv(country_mapping)
    cgrt = clean_cgrt(
        url=bsg_latest,
        columns_rename={
            "Date": "date",
            "StringencyIndex_Average": "stringency_index",
        },
        country_mapping=country_mapping,
    )
    cgrt_diff = clean_cgrt(
        url=bsg_diff_latest,
        columns_rename={
            "Date": "date",
            "StringencyIndex_NonVaccinated": "stringency_index_nonvac",
            "StringencyIndex_Vaccinated": "stringency_index_vac",
            "StringencyIndex_WeightedAverage": "stringency_index_weighted_avg",
        },
        country_mapping=country_mapping,
    )
    cgrt = cgrt.merge(cgrt_diff, on=["location", "date"], how="outer")
    return cgrt


def clean_cgrt(url, columns_rename, country_mapping):
    # Read file
    df = pd.read_csv(url, low_memory=False)
    # Filter rows
    if "RegionCode" in df.columns:
        df = df[df.RegionCode.isnull()]
    columns = list(columns_rename.keys())
    # Filter columns
    df = df[columns + ["CountryName"]]
    # Format date
    df.loc[:, "Date"] = pd.to_datetime(df["Date"], format="%Y%m%d").dt.date.astype(str)
    # Merge with country mapping
    df = country_mapping.merge(df, on="CountryName", how="right")
    # Check missing countries
    missing_from_mapping = df[df["Country"].isna()]["CountryName"].unique()
    if len(missing_from_mapping) > 0:
        raise Exception(f"Missing countries in OxCGRT mapping: {missing_from_mapping}")
    # Final column transformations
    df = df.rename(
        columns={
            "Country": "location",
            **columns_rename,
        }
    ).drop(columns=["CountryName"])
    return df

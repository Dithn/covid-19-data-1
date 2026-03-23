import pandas as pd

from cowidev.utils.clean.dates import clean_date, localdate
from cowidev.utils.utils import check_known_columns
from cowidev.utils.web.download import read_csv_from_url
from cowidev.vax.utils.orgs import ECDC_VACCINES
from cowidev.vax.utils.base import CountryVaxBase
from cowidev import PATHS
from cowidev.vax.utils.utils import build_vaccine_timeline


AGE_GROUPS_KNOWN = {
    "ALL",
    "Age0_4",
    "Age15_17",
    "Age5_9",
    "Age10_14",
    "Age<18",
    "Age18_24",
    "Age25_49",
    "Age50_59",
    "Age60_69",
    "Age70_79",
    "1_Age<60",
    "1_Age60+",
    "Age80+",
    "AgeUNK",
    "HCW",
    "LTCF",
}


AGE_GROUPS_MUST_HAVE = {
    "Age18_24",
    "Age25_49",
    "Age50_59",
    "Age60_69",
    "Age70_79",
    "Age80+",
}


AGE_GROUP_UNDERAGE_LEVELS = {
    "lvl0": "Age<18",
    "lvl1": {
        "Age0_4",
        "Age5_9",
        "Age10_14",
        "Age15_17",
    },
}


AGE_GROUPS_UNDERAGE = {AGE_GROUP_UNDERAGE_LEVELS["lvl0"]} | AGE_GROUP_UNDERAGE_LEVELS["lvl1"]


AGE_GROUPS_RELEVANT = AGE_GROUPS_UNDERAGE | AGE_GROUPS_MUST_HAVE


LOCATIONS_MAIN_INCLUDED = [
    "Austria",
    "Portugal",
    "Netherlands",
    "Denmark",
]

LOCATIONS_AGE_EXCLUDED = [
    "Switzerland",
    "Germany",
]

LOCATIONS_MANUFACTURER_EXCLUDED = [
    "Czechia",
    "France",
    "Germany",
    "Italy",
    "Latvia",
    "Romania",
    "Iceland",
    "Switzerland",
]


VACCINES_ONE_DOSE = ["JANSS"]


COLUMNS = {
    "Denominator",
    "FirstDose",
    "FirstDoseRefused",
    "NumberDosesReceived",
    "Population",
    "Region",
    "ReportingCountry",
    "SecondDose",
    "TargetGroup",
    "UnknownDose",
    "Vaccine",
    "YearWeekISO",
    "DoseAdditional1",
    "DoseAdditional2",
    "DoseAdditional3",
    "DoseAdditional4",
    "DoseAdditional5",
    "NumberDosesExported",
}

MANUF_LOCATIONS_OUTLIERS = {
    "Cyprus": {
        "Moderna": {
            "date_min": "2023-02-17",
            "date_max": "2023-09-15",
        },
        "Pfizer/BioNTech": {
            "date_min": "2023-02-17",
            "date_max": "2023-09-15",
        },
    },
    "Denmark": {
        "Pfizer/BioNTech": {
            # Remove datapoints between date_min and date_max
            "date_min": "2023-07-14",
            "date_max": "2023-09-29",
            # Remove datapoins with these dates
            "dates": [
                "2023-05-12",
                "2023-06-23",
                "2023-06-30",
                "2023-07-07",
            ]
        },
    },
    "Ireland": {
        "Pfizer/BioNTech": {
            "date_min": "2023-06-30",
            "date_max": "2023-09-15",
        },
        "Moderna": {
            "date_min": "2023-06-30",
            "date_max": "2023-09-15",
            "dates": [
                "2023-03-03",
                "2023-03-31",
                "2023-04-07",
                "2023-04-14",
                "2023-04-21",
            ]
        },
    },
    "Norway": {
        "Pfizer/BioNTech": {
            "date_min": "2023-06-30",
            "date_max": "2023-09-11",
            # Remove datapoints after this date that have values lower that in this date
            "dates_after_if_lower": ["2023-02-10"],
        },
        "Moderna": {
            "dates": [
                "2023-03-03",
                "2023-06-02",
                "2023-07-07",
                "2023-07-14",
                "2023-07-28",
                "2023-08-04",
                "2023-08-11",
                "2023-08-25",
                "2023-09-01",
            ],
            "dates_after_if_lower": ["2023-02-10"],
        },
    },
    "Slovenia": {
        "Moderna": {
            "dates_after_if_lower": ["2022-10-07"],
        },
        "Pfizer/BioNTech": {
            "dates_after_if_lower": ["2022-10-07"],
        }
    },
    "Portugal": {
        "Moderna": {
            "dates_after_if_lower": ["2023-02-10"],
        },
        "Pfizer/BioNTech": {
            "dates_after_if_lower": ["2023-02-10"],
        }
    },
}

class ECDC(CountryVaxBase):
    location = "ECDC"
    source_url = "https://opendata.ecdc.europa.eu/covid19/vaccine_tracker/csv/data.csv"
    source_url_ref = "https://www.ecdc.europa.eu/en/publications-data/data-covid-19-vaccination-eu-eea"
    vaccine_mapping = {**ECDC_VACCINES, "UNK": "Unknown", "OTHER": "Unknown"}

    @property
    def country_mapping(self):
        return self._load_country_mapping(PATHS.INTERNAL_INPUT_ISO_FULL_FILE)

    def read(self):
        # df = pd.read_csv("/home/lucas/repos/covid-19-data/ECDC data.csv")
        df = read_csv_from_url(self.source_url, timeout=40)
        return df

    def _load_country_mapping(self, iso_path: str):
        country_mapping = pd.read_csv(iso_path)
        return dict(zip(country_mapping["alpha-2"], country_mapping["location"]))

    def _weekday_to_date(self, d):
        new_date = clean_date(d + "+5", "%Y-W%W+%w")
        if new_date > localdate("Europe/London"):
            new_date = clean_date(d + "+2", "%Y-W%W+%w")
        return new_date

    def pipe_initial_check(self, df: pd.DataFrame) -> pd.DataFrame:
        # TODO: to be removed
        # Currently some rows have NaN in the Vaccine column. We assume that these are UNK for now.
        # I have reached out to ECDC to ask about this.
        # assert set(df.loc[df["Vaccine"].isna(), "ReportingCountry"]) == {
        #     "FR",
        #     "IE",
        # }, "Different number of countries with Vaccine=NaN found!"
        assert df["Vaccine"].isna().sum() == 0, "More Vaccine=NaN detected!"
        # df.loc[df["Vaccine"].isna(), "Vaccine"] = "UNK"
        # Vaccines
        vaccines_wrong = set(df.Vaccine).difference(self.vaccine_mapping)
        if vaccines_wrong:
            raise ValueError(f"Unknown vaccines found. Check {vaccines_wrong}")
        check_known_columns(df, COLUMNS)
        return df

    def pipe_base(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.pipe(self.pipe_initial_check)
        df = df.assign(
            total_vaccinations=df[
                ["FirstDose", "SecondDose", "UnknownDose", "DoseAdditional1", "DoseAdditional2", "DoseAdditional3", "DoseAdditional4", "DoseAdditional5"]
            ].sum(axis=1),
            people_vaccinated=df.FirstDose,
            people_fully_vaccinated=df.SecondDose,
            people_with_booster=df.DoseAdditional1,
            total_boosters=df["DoseAdditional1"] + df["DoseAdditional2"] + df["DoseAdditional3"] + df["DoseAdditional4"] + df["DoseAdditional5"],
            date=df.YearWeekISO.apply(self._weekday_to_date),
            location=df.ReportingCountry.replace(self.country_mapping),
        )
        # Update people_fully_vaccinated
        mask = df.Vaccine.isin(VACCINES_ONE_DOSE)
        df.loc[mask, "people_fully_vaccinated"] = df.loc[mask, "people_fully_vaccinated"] + df.loc[mask, "FirstDose"]
        return df.loc[df.Region.isin(self.country_mapping.keys())]

    def _vaccine_timeseries(self, df: pd.DataFrame):
        """Get Series with the vaccine timeseries for all countries.

        Format:
            location -> {vaccine_1: start_date_1, vaccine_2: start_date_2, ...}
        """
        x = df[df.Vaccine.isin(ECDC_VACCINES)]
        x = x.assign(Vaccine=x.transform({"Vaccine": lambda x: ECDC_VACCINES[x]}))
        x = x[x["total_vaccinations"].fillna(0) > 1]
        vaccine_timeseries = (
            x.groupby(["location", "Vaccine"], as_index=False)
            .date.min()
            .groupby("location")
            .apply(lambda x: x.set_index("Vaccine")["date"].to_dict())
        )
        return vaccine_timeseries

    def pipe_group(self, df: pd.DataFrame, group_field: str = None, group_field_renamed: str = None) -> pd.DataFrame:
        if group_field is None:
            cols_group = ["date", "location"]
            cols_rename = {}
        else:
            cols_group = ["date", "location", group_field]
            cols_rename = {group_field: group_field_renamed}
        return (
            df.groupby(cols_group, as_index=False)[
                [
                    "total_vaccinations",
                    "people_vaccinated",
                    "people_fully_vaccinated",
                    "people_with_booster",
                    "total_boosters",
                    "UnknownDose",
                ]
            ]
            .sum()
            .rename(columns=cols_rename)
        )

    def pipe_cumsum(self, df: pd.DataFrame, group_field_renamed: str = None) -> pd.DataFrame:
        if group_field_renamed is None:
            cols_group = ["location"]
        else:
            cols_group = ["location", group_field_renamed]
        return df.assign(
            total_vaccinations=df.groupby(cols_group)["total_vaccinations"].cumsum(),
            people_vaccinated=df.groupby(cols_group)["people_vaccinated"].cumsum(),
            people_fully_vaccinated=df.groupby(cols_group)["people_fully_vaccinated"].cumsum(),
            people_with_booster=df.groupby(cols_group)["people_with_booster"].cumsum(),
            total_boosters=df.groupby(cols_group)["total_boosters"].cumsum(),
            UnknownDose=df.groupby(cols_group)["UnknownDose"].cumsum(),
        )

    def pipeline_common(
        self, df: pd.DataFrame, group_field: str = None, group_field_renamed: str = None
    ) -> pd.DataFrame:
        cols = [
            "date",
            "location",
            "total_vaccinations",
            "people_vaccinated",
            "people_fully_vaccinated",
            "people_with_booster",
            "total_boosters",
            "UnknownDose",
        ]
        if group_field_renamed is not None:
            cols = cols + [group_field_renamed]

        return (
            df.pipe(self.pipe_group, group_field, group_field_renamed)[cols]
            .sort_values("date")
            .pipe(self.pipe_cumsum, group_field_renamed)
        )

    def pipe_filter_locations(self, df: pd.DataFrame):
        """Filters countries to be excluded and those with a high number of"""
        return df[df.location.isin(LOCATIONS_MAIN_INCLUDED)]

    def pipe_vaccine(self, df: pd.DataFrame, vax_timeline):
        dfs = []
        locations = df.location.unique()
        for location in locations:
            df_c = df[df.location == location]
            df_c = build_vaccine_timeline(df_c, vax_timeline[location])
            dfs.append(df_c)
        return pd.concat(dfs, ignore_index=True)

    def pipe_filter_targetgroup(self, df: pd.DataFrame):
        dfs = []
        dfg = df.groupby("location")
        for _, _df in dfg:
            if "Age<18" in _df.TargetGroup.unique():
                tagetgroups = ["ALL", "Age<18"]
            else:
                tagetgroups = ["ALL"] + list(AGE_GROUP_UNDERAGE_LEVELS["lvl1"])
            _df = _df.loc[df.TargetGroup.isin(tagetgroups)]
            dfs.append(_df)
        df = pd.concat(dfs)
        return df

    def pipeline(self, df: pd.DataFrame):
        vax_timeline = self._vaccine_timeseries(df)
        df = (
            df.pipe(self.pipe_filter_targetgroup)
            .pipe(self.pipeline_common)
            .pipe(self.pipe_filter_locations)
            .pipe(self.pipe_vaccine, vax_timeline)
            .assign(source_url=self.source_url_ref)
        )
        # Boosters (people -> doses)
        df = df.assign(total_boosters=df.people_with_booster)
        return df[
            [
                "location",
                "date",
                "vaccine",
                "source_url",
                "total_vaccinations",
                "people_vaccinated",
                "people_fully_vaccinated",
                "total_boosters",
            ]
        ]

    def pipe_rename_vaccines(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.assign(vaccine=df.vaccine.replace(self.vaccine_mapping))
        df = df.groupby(["location", "date", "vaccine"], as_index=False).sum()
        return df

    def pipe_manufacturer_filter_locations(self, df: pd.DataFrame):
        """Filters countries to be excluded and those with a high number of unknown doses."""

        def _get_perc_unk(x):
            res = x.groupby("vaccine").total_vaccinations.sum()
            res /= res.sum()
            if not "Unknown" in res:
                return 0
            return res.loc["Unknown"]

        threshold_unk_ratio = 0.05
        mask = df.groupby("location").apply(_get_perc_unk) < threshold_unk_ratio
        locations_valid = mask[mask].index.tolist()
        locations_valid = [loc for loc in locations_valid if loc not in LOCATIONS_MANUFACTURER_EXCLUDED]
        df = df[df.location.isin(locations_valid)]
        return df

    def pipe_manufacturer_filter_entries(self, df: pd.DataFrame):
        return df[~df.vaccine.isin(["Unknown"])]

    def pipeline_manufacturer(self, df: pd.DataFrame):
        group_field_renamed = "vaccine"
        return (
            df.loc[df.TargetGroup.isin(["ALL", "Age<18"])]
            .pipe(self.pipeline_common, "Vaccine", group_field_renamed)
            .pipe(self.pipe_rename_vaccines)
            .pipe(self.pipe_manufacturer_filter_locations)
            .pipe(self.pipe_manufacturer_filter_entries)[["location", "date", "vaccine", "total_vaccinations"]]
            .sort_values(["location", "date", "vaccine"])
        )

    def pipe_age_checks(self, df: pd.DataFrame) -> pd.DataFrame:
        # Check all age groups are valid names
        ages_groups_wrong = set(df.age_group).difference(AGE_GROUPS_KNOWN)
        if ages_groups_wrong:
            raise ValueError(f"Unknown age groups found. Check {ages_groups_wrong}")
        return df

    def pipe_age_filter_locations(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter locations and keep only valid ones.

        Validity is defined as a country having all age groups defined by `AGE_GROUPS_MUST_HAVE`.
        """
        locations = df.location.unique()
        locations_valid = []
        for location in locations:
            df_c = df.loc[df.location == location]
            if not AGE_GROUPS_MUST_HAVE.difference(df_c.age_group.unique()):
                locations_valid.append(location)
        locations_valid = [loc for loc in locations_valid if loc not in LOCATIONS_AGE_EXCLUDED]
        df = df[df.location.isin(locations_valid)]
        return df

    def pipe_age_filter_entries(self, df: pd.DataFrame) -> pd.DataFrame:
        """More granular filter. Keep entries where data is deemed reliable.

        1. Checks field ALL is equal to sum of all other ages (within 5% error). If not filters rows out.
        2. If percentage of unknown doses is above 5% of total doses, filters row out.
        """
        # Find valid dates + location
        x = df.pivot(index=["date", "location"], columns="age_group", values="total_vaccinations").reset_index()
        x = x.dropna(subset=AGE_GROUPS_MUST_HAVE, how="any")
        # Create debug variable (= sum of all ages)
        x = x.assign(
            debug_u18=x[AGE_GROUP_UNDERAGE_LEVELS["lvl0"]].fillna(x[AGE_GROUP_UNDERAGE_LEVELS["lvl1"]].sum(axis=1))
        )
        x = x.assign(debug=x[AGE_GROUPS_MUST_HAVE].sum(axis=1) + x.debug_u18)
        x = x.assign(
            debug_diff=x.ALL - x.debug,
            debug_diff_perc=(x.ALL - x.debug) / x.ALL,
        )
        threshold_missmatch_ratio = 0.05  # Keep only those days where missmatch between sum(ages) and total is <5%
        x = x[x.debug_diff_perc <= threshold_missmatch_ratio]
        valid_entries_ids = x[["date", "location"]]
        if not valid_entries_ids.value_counts().max() == 1:
            raise ValueError("Some entries appear to be duplicated")
        df = df.merge(valid_entries_ids, on=["date", "location"])

        # Filter entries with too many unknown doses (where more 5% of doses are unknown)
        threshold_unknown_doses_ratio = 0.05
        df = df[(df.UnknownDose / df.total_vaccinations) < threshold_unknown_doses_ratio]
        return df

    def pipe_age_groups(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build age groups."""
        # df = df[~df.age_group.isin(['LTCF', 'HCW', 'AgeUNK', 'ALL'])]
        df_ = df[df.age_group.isin(AGE_GROUPS_RELEVANT)].copy()
        df_ = df_.assign(age_group_modified=df_.age_group.replace({"Age<18": "Age0_17"}))
        regex = r"(?:1_)?Age(\d{1,2})?(?:\+|<)?_?(\d{1,2})?"
        df_[["age_group_min", "age_group_max"]] = df_.age_group_modified.str.extract(regex)
        # df_ = df_.assign(age_group_min=df_.age_group_min.fillna(0))
        # df.loc[df.age_group == "1_Age60+", ["age_group_min", "age_group_max"]] = [60, pd.NA]
        # df.loc[df.age_group == "1_Age<60", ["age_group_min", "age_group_max"]] = [0, 60]
        return df_

    def pipe_age_relative_metrics(self, df: pd.DataFrame, df_og: pd.DataFrame) -> pd.DataFrame:
        df_den = df_og.loc[df_og.TargetGroup.isin(AGE_GROUPS_RELEVANT)].dropna(subset=["Denominator"])
        if df_den.Denominator.isnull().any():
            raise ValueError(f"Denomintor found to be null: {df_den[df_den.Denominator.isnull()]}")
        res = df_den.groupby(["date", "location", "TargetGroup"]).Denominator.nunique()
        if (res != 1).any():
            raise ValueError(
                "Several Denomintor values found for same (date, location, TargetGroup):"
                f" {res[res== 1].index.tolist()}"
            )
        df_den = df_den[["date", "location", "TargetGroup", "Denominator"]].drop_duplicates()
        df = df.merge(
            df_den,
            left_on=["date", "age_group", "location"],
            right_on=["date", "TargetGroup", "location"],
        )
        return df.assign(
            people_vaccinated_per_hundred=(100 * df.people_vaccinated / df.Denominator).round(2),
            people_fully_vaccinated_per_hundred=(100 * df.people_fully_vaccinated / df.Denominator).round(2),
            people_with_booster_per_hundred=(100 * df.people_with_booster / df.Denominator).round(2),
        )

    def pipeline_age(self, df: pd.DataFrame):
        group_field_renamed = "age_group"
        return (
            df
            # .dropna(subset=["Denominator"])
            .pipe(self.pipeline_common, "TargetGroup", group_field_renamed)
            .pipe(self.pipe_age_checks)
            .pipe(self.pipe_age_filter_locations)
            .pipe(self.pipe_age_filter_entries)
            .pipe(self.pipe_age_groups)
            .pipe(self.pipe_age_relative_metrics, df)
            .drop(columns=[group_field_renamed])
            .sort_values(["location", "date", "age_group_min"])
        )

    def _filter_age_targetgroup(self, df_c: pd.DataFrame):
        # Filter age groups
        date_0 = df_c.loc[df_c.TargetGroup.isin({AGE_GROUP_UNDERAGE_LEVELS["lvl0"]}), "date"].unique()
        date_1 = df_c.loc[df_c.TargetGroup.isin(AGE_GROUP_UNDERAGE_LEVELS["lvl1"]), "date"].unique()
        if (len(date_0) == len(date_1)) | (len(date_0) == 0):
            age_group_selection = AGE_GROUPS_MUST_HAVE | AGE_GROUP_UNDERAGE_LEVELS["lvl1"]
        elif len(date_1) == 0:
            age_group_selection = AGE_GROUPS_MUST_HAVE | {AGE_GROUP_UNDERAGE_LEVELS["lvl0"]}
        else:
            if (df_c.location == "Ireland").any():
                age_group_selection = AGE_GROUPS_MUST_HAVE | AGE_GROUP_UNDERAGE_LEVELS["lvl1"]
            else:
                raise ValueError(
                    f"Can't choose between under age groups. Restriction might be too strict, consider relaxing it!"
                )
        df_c = df_c[df_c.TargetGroup.isin(age_group_selection)]
        return df_c

    def export_age(self, df: pd.DataFrame):
        df_age = df.pipe(self.pipeline_age)
        # Export
        locations = df_age.location.unique()
        for location in locations:
            df_c = df_age[df_age.location == location].pipe(self._filter_age_targetgroup).copy()
            self.export_datafile(
                df_age=df_c,
                filename=location,
                meta_age={
                    "source_name": "European Centre for Disease Prevention and Control (ECDC)",
                    "source_url": self.source_url_ref,
                },
            )

    def export_manufacturer(self, df: pd.DataFrame):
        df_manufacturer = df.pipe(self.pipeline_manufacturer)
        # Export
        locations = df_manufacturer.location.unique()
        for location in locations:
            # Filter to keep only country-relevant data
            df_c = df_manufacturer[df_manufacturer.location == location].copy()
            # Filter some dates
            if location in MANUF_LOCATIONS_OUTLIERS:
                for vaccine, dates in MANUF_LOCATIONS_OUTLIERS[location].items():
                    if ("date_min" in dates) and ("date_max" in dates):
                        msk = (df_c.vaccine == vaccine) & (df_c.date >= dates["date_min"]) & (df_c.date <= dates["date_max"])
                        df_c = df_c.loc[~msk]
                    if "dates" in dates:
                        msk = (df_c.vaccine == vaccine) & (df_c.date.isin(dates["dates"]))
                        df_c = df_c.loc[~msk]
                    if "dates_after_if_lower" in dates:
                        for d in dates["dates_after_if_lower"]:
                            value = df_c.loc[(df_c["date"] == d) & (df_c["vaccine"] == vaccine), "total_vaccinations"]
                            if not value.empty:
                                value = value.values[0]
                                msk = (df_c.vaccine == vaccine) & (df_c.date >= d) & (df_c.total_vaccinations < value)
                                df_c = df_c.loc[~msk]
            df_c = self.make_monotonic(df_c, "vaccine")
            self.export_datafile(
                df_manufacturer=df_c,
                filename=location,
                meta_manufacturer={
                    "source_name": "European Centre for Disease Prevention and Control (ECDC)",
                    "source_url": self.source_url_ref,
                },
                # attach_manufacturer=True,
            )

    def export_main(self, df: pd.DataFrame):
        df = df.pipe(self.pipeline)
        # Export
        locations = df.location.unique()
        for location in locations:
            df_c = df[df.location == location].copy()
            msk = (
                df_c[["total_vaccinations", "people_vaccinated", "people_fully_vaccinated", "total_vaccinations"]].sum(
                    axis=1
                )
                != 0
            )
            df_c = df_c.loc[msk]
            s0 = df_c.shape
            df_c = self.make_monotonic(df_c)
            s1 = df_c.shape
            assert s0 == s1, f"make_monotonic changed shape from {s0} to {s1}"
            self.export_datafile(df_c, filename=location)

    def export(self):
        # Read data
        df = self.read().pipe(self.pipe_base)
        # Main
        self.export_main(df)
        # Age
        self.export_age(df)
        # Manufacturer
        self.export_manufacturer(df)


def main():
    ECDC().export()

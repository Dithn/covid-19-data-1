import os
from sys import modules
import time
import importlib
import json
from datetime import date

from joblib import Parallel, delayed
import pandas as pd
from pandas.api.types import is_string_dtype

from cowidev import PATHS
from cowidev.utils.log import get_logger


logger = get_logger()


class HospETL:
    def extract(
        self,
        modules: list,
        parallel: bool = False,
        n_jobs: int = -2,
        modules_skip: list = [],
    ):
        """Get the data for all locations.

        - Build preliminary dataframe with all locations data.
        - Build metadata dataframe with locations metadata (source url, source name, etc.)
        """
        t0 = time.time()
        # Sources
        modules = [s for s in modules if s not in modules_skip]
        if modules == []:
            logger.info("HOSP - No data to be collected (check skipped countries)...")
            return None
        # Get data
        modules_execution_results = self.extract_collect(parallel, n_jobs, modules=modules)
        self._execution_summary(t0, modules_execution_results)
        # Export data (checkpoint)
        self.extract_export_checkpoint(modules_execution_results)
        # Process output
        df, df_meta = self.extract_process()
        return {"df": df, "meta": df_meta}

    def extract_collect(self, parallel, n_jobs, modules):
        """Collects data for all countries"""
        logger.info("HOSP - Collecting data...")
        if parallel:
            modules_execution_results = Parallel(n_jobs=n_jobs, backend="threading")(
                delayed(self._extract_entity)(
                    m,
                )
                for m in modules
            )
        else:
            modules_execution_results = [self._extract_entity(m) for m in modules]
        return modules_execution_results

    def extract_export_checkpoint(self, modules_execution_results):
        """Exports downloaded data and metadata."""
        logger.info("HOSP - Saving checkpoint data...")
        for m in modules_execution_results:
            if m is not None:
                df = m[0]
                metadata = m[1]
                if isinstance(metadata, list):
                    for metadata_ in metadata:
                        df_ = df[df.entity == metadata_["entity"]]
                        df_.to_csv(
                            os.path.join(PATHS.INTERNAL_OUTPUT_HOSP_MAIN_DIR, f"{metadata_['entity']}.csv"),
                            index=False,
                        )
                        with open(
                            os.path.join(PATHS.INTERNAL_OUTPUT_HOSP_META_DIR, f"{metadata_['entity']}.json"), "w"
                        ) as outfile:
                            json.dump(metadata_, outfile)
                else:
                    df.to_csv(
                        os.path.join(PATHS.INTERNAL_OUTPUT_HOSP_MAIN_DIR, f"{metadata['entity']}.csv"), index=False
                    )
                    with open(
                        os.path.join(PATHS.INTERNAL_OUTPUT_HOSP_META_DIR, f"{metadata['entity']}.json"), "w"
                    ) as outfile:
                        json.dump(metadata, outfile)

    def extract_process(self):
        """Load checkpointed data."""
        logger.info("HOSP - Loading checkpoint data...")
        # Load & build data
        data_paths = [
            os.path.join(PATHS.INTERNAL_OUTPUT_HOSP_MAIN_DIR, p)
            for p in os.listdir(PATHS.INTERNAL_OUTPUT_HOSP_MAIN_DIR)
            if p[-3:] == "csv"
        ]
        df = pd.concat([pd.read_csv(p) for p in data_paths])
        # Load & buildmetadata
        metadata_paths = [
            os.path.join(PATHS.INTERNAL_OUTPUT_HOSP_META_DIR, p)
            for p in os.listdir(PATHS.INTERNAL_OUTPUT_HOSP_META_DIR)
        ]
        metadata = []
        for p in metadata_paths:
            with open(p, "r") as infile:
                metadata.append(json.load(infile))
        df_meta = self._build_metadata(metadata)
        # Process output
        df = df.dropna(subset=["value"])

        # Remove duplicates
        df = df.drop_duplicates()  # subset=["date", "indicator", "entity"])

        # Weird things
        df = df[
            ~(
                (
                    (df.entity == "Serbia")
                    & (df.date == "2020-03-09")
                    & (df.indicator == "Daily hospital occupancy")
                    & (df.value == 2)
                )
                | (
                    (df.entity == "Malta")
                    & (df.date == "2022-10-09")
                    & (df.indicator == "Weekly new hospital admissions")
                )
                | (
                    (df.entity == "Malta")
                    & (df.date == "2022-10-16")
                    & (df.indicator == "Weekly new hospital admissions")
                )
                | (
                    (df.entity == "Malta")
                    & (df.date == "2022-10-23")
                    & (df.indicator == "Weekly new hospital admissions")
                )
            )
        ]
        # Check
        duplicates = df[df.duplicated(subset=["date", "entity", "indicator"], keep=False)]
        if len(duplicates) > 0:
            raise Exception(f"Some entity-date-indicator combinations are present more than once! {duplicates}")

        return df, df_meta

    def _build_metadata(self, metadata):
        """Build metadata dataframe (to be exported later to locations.csv)."""
        # Flatten list
        metadata = [[m] if not isinstance(m, list) else m for m in metadata]
        metadata = [mm for m in metadata for mm in m]
        # Build dataframe
        metadata = [
            {"location": m["entity"], "source_name": m["source_name"], "source_website": m["source_url_ref"]}
            for m in metadata
        ]
        df_meta = pd.DataFrame.from_records(metadata)
        return df_meta

    def _extract_entity(self, module_name: str):
        """Execute the process to get the data for a certain location (country)."""
        t0 = time.time()
        module = importlib.import_module(module_name)
        logger.info(f"HOSP - {module_name}: started")
        try:
            df, metadata = module.main()
        except Exception as err:
            logger.error(f"HOSP - {module_name}: ❌ {err}", exc_info=True)
            # raise Exception(f"Process for {module_name} did not work! Please check.")
            # return None
        else:
            self._check_fields_df(df)
            # Execution details
            t = round(time.time() - t0, 2)
            execution = {
                "module_name": module_name,
                "time": t,
            }
            logger.info(f"HOSP - {module_name}: SUCCESS ✅")
            return df, metadata, execution

    def _check_fields_df(self, df):
        """Check format of the data collected for a certain location."""
        assert df.indicator.isin(
            {
                "Daily hospital occupancy",
                "Daily ICU occupancy",
                "Weekly new hospital admissions",
                "Weekly new ICU admissions",
            }
        ).all(), "One of the indicators for this country is not recognized!"
        # check date
        assert is_string_dtype(df.date), "The date column is not a string!"
        dt = date.today().strftime("%Y-%m-%d")
        if (msk := df["date"] > dt).any():
            ent = df.loc[msk, "entity"].values[0]
            dt = set(df.loc[msk, "date"])
            error_msg = f"The date column contains dates in the future! Entity `{ent}` has date(s): `{dt}`"
            raise ValueError(error_msg)

    def _build_time_df(self, execution):
        """Build execution time dataframe."""
        df_time = (
            pd.DataFrame([{"module": m["module_name"], "execution_time (sec)": m["time"]} for m in execution])
            .set_index("module")
            .sort_values(by="execution_time (sec)", ascending=False)
        )
        return df_time

    def _execution_summary(self, t0, modules_execution_results):
        """Print a summary from the execution (timings)."""
        execution = [m[2] for m in modules_execution_results if m is not None]
        df_time = self._build_time_df(execution)
        t_sec_1 = round(time.time() - t0, 2)
        t_min_1 = round(t_sec_1 / 60, 2)
        print("---")
        print("TIMING DETAILS")
        print(f"Took {t_sec_1} seconds (i.e. {t_min_1} minutes).")
        print(f"Top most time consuming scripts:")
        print(df_time.head(20))
        print("---")

    def pipe_metadata(self, df):
        print("Adding ISO & population…")
        shape_og = df.shape
        population = _load_population()
        df = df.merge(population, on="entity")
        if shape_og[0] != df.shape[0]:
            raise ValueError(f"Dimension 0 after merge is different: {shape_og[0]} --> {df.shape[0]}")
        return df

    def pipe_per_million(self, df):
        print("Adding per-capita metrics…")
        per_million = df.copy()
        per_million.loc[:, "value"] = per_million["value"].div(per_million["population"]).mul(1000000).round(3)
        per_million.loc[:, "indicator"] = per_million["indicator"] + " per million"
        df = pd.concat([df, per_million], ignore_index=True).drop(columns="population")
        return df

    def pipe_round_values(self, df):
        df.loc[-df.indicator.str.contains("per million"), "value"] = df.value.round()
        return df

    def transform(self, df: pd.DataFrame):
        return (
            df.pipe(self.pipe_metadata)
            .pipe(self.pipe_per_million)
            .pipe(self.pipe_round_values)[["entity", "iso_code", "date", "indicator", "value"]]
            .sort_values(["entity", "date", "indicator"])
        )

    def transform_meta(self, df_meta: pd.DataFrame, df: pd.DataFrame, locations_path: str):
        # Get most recent date of data update
        df_ = (
            df.groupby(["entity", "iso_code"], as_index=False)
            .date.max()
            .rename(columns={"date": "last_observation_date"})
        )
        # Add iso and observation date to dataframe
        df_meta = df_meta.merge(df_, left_on="location", right_on="entity", how="left")
        # Fill with locations' metadata of countries not updated in this batch
        # df_meta_current = pd.read_csv(locations_path)
        # df_meta = (
        #     pd.concat([df_meta, df_meta_current])
        #     .sort_values("last_observation_date")
        #     .drop_duplicates(subset=["location"])
        # )
        # Order columns
        df_meta = df_meta[
            ["location", "iso_code", "last_observation_date", "source_name", "source_website"]
        ].sort_values("location")
        return df_meta

    def load(self, df: pd.DataFrame, output_path: str) -> None:
        # Export data
        df.to_csv(output_path, index=False)

    def run(self, parallel: bool, n_jobs: int, modules, modules_skip=[]):
        data = self.extract(parallel=parallel, n_jobs=n_jobs, modules=modules, modules_skip=modules_skip)
        if data is not None:
            df = self.transform(data["df"])
            df_meta = self.transform_meta(data["meta"], df, PATHS.DATA_HOSP_META_FILE)
            self.load(df, PATHS.DATA_HOSP_MAIN_FILE)
            self.load(df_meta, PATHS.DATA_HOSP_META_FILE)


def _load_population():
    population = pd.read_csv(PATHS.INTERNAL_INPUT_UN_POPULATION_FILE, usecols=["entity", "iso_code", "population"])
    population_sub = pd.read_csv(
        PATHS.INTERNAL_INPUT_OWID_POPULATION_SUB_FILE, usecols=["location", "iso_code", "population"]
    ).rename(columns={"location": "entity"})
    population = pd.concat([population, population_sub], ignore_index=True)
    return population


def run_etl(parallel: bool, n_jobs: int, modules: list, modules_skip: list = []):
    etl = HospETL()
    etl.run(parallel, n_jobs, modules=modules, modules_skip=modules_skip)

library(data.table)
library(dplyr)
library(ggplot2)
library(googlesheets4)
library(imputeTS)
library(lubridate)
library(readr)
library(retry)
library(rjson)
library(stringr)
library(tidyr)
library(zoo)
rm(list = ls())

TESTING_FOLDER <- dirname(rstudioapi::getSourceEditorContext()$path)
setwd(TESTING_FOLDER)
CONFIG <- rjson::fromJSON(file = "testing_dataset_config.json")
Sys.setlocale("LC_TIME", "en_US")

# Utils
source("smoother.R")

# Offset date for grapher dataset
origin_date <- ymd("2020-01-21")

population <- fread("../../input/un/population_latest.csv")
population <- population[, .(Country = entity, Population = population)]

# Find sheets marked as Collate = TRUE in METADATA
gs4_auth(email = CONFIG$google_credentials_email)
key <- CONFIG$covid_time_series_gsheet
retry(
    expr = {metadata <- read_sheet(key, sheet = "METADATA", range = "A2:L300") %>% filter(Collate == TRUE)},
    when = "RESOURCE_EXHAUSTED",
    max_tries = 10,
    interval = 20
)
stopifnot("Detailed description" %in% names(metadata))
sheet_names <- sort(metadata$Sheet)

# Cut-off periods
cutoff <- fread("../../input/owid/testing_cutoffs.csv")

# Import cases from latest online version rather than local to avoid desync
confirmed_cases <- fread("https://covid.ourworldindata.org/data/owid-covid-data.csv",
                         showProgress = FALSE, select = c("date", "location", "new_cases_smoothed", "total_cases"))
setnames(confirmed_cases, c("date", "location"), c("Date", "Country"))
confirmed_cases[, Date := ymd(Date)]

# Process each country's data
parse_country <- function(sheet_name) {
    message(sheet_name)
    is_automated <- metadata %>% filter(Sheet == sheet_name) %>% pull("Automated")
    stopifnot(length(is_automated) == 1)

    if (is_automated) {
        filepath <- sprintf("../../output/testing/main_data/%s.csv", sheet_name)
        collated <- suppressMessages(read_csv(filepath))
        stopifnot(all(!is.na(collated$Date)))
    } else {
        retry(
            expr = {collated <- suppressMessages(read_sheet(key, sheet = sheet_name))},
            when = "RESOURCE_EXHAUSTED",
            max_tries = 10,
            interval = 20
        )
    }
    
    stopifnot(length(table(collated$Units)) == 1)
    stopifnot(collated$Units[1] %in% c("people tested", "samples tested", "tests performed", "units unclear"))

    collated <- collated %>%
        filter(!is.na(Country) & !is.na(Date)) %>%
        select(Country, Units, Date, `Source URL`, `Source label`, Notes,
               matches("^Cumulative total$"),
               matches("^Daily change in cumulative total$"),
               matches("^Positive rate$"))

    collated <- collated %>%
        inner_join(population, by = "Country") %>%
        arrange(Date) %>%
        mutate(Sheet = sheet_name) %>%
        mutate(Date = date(Date))

    stopifnot(nrow(collated) > 0)

    # Censor recent data when needed, based on /scripts/input/owid/testing_cutoffs.csv
    if (sheet_name %in% cutoff$country_sheet) {
        cutoff_period <- cutoff %>% filter(country_sheet == sheet_name) %>% pull(cutoff_days)
        collated <- collated %>% filter(Date < (today() - cutoff_period))
        message(sprintf("Applied cut-off of %s days for %s", cutoff_period, sheet_name))
    }

    # Calculate daily change when absent
    if (!"Daily change in cumulative total" %in% names(collated)) {
        collated <- collated %>%
            mutate(`Daily change in cumulative total` = `Cumulative total` - lag(`Cumulative total`, 1, default = 0)) %>%
            mutate(`Daily change in cumulative total` = if_else(lag(Date, 1) + duration(1, "day") == Date,
                                                                `Daily change in cumulative total`, NA_real_))
    }

    # Calculate cumulative total when absent
    if (!"Cumulative total" %in% names(collated)) {
        collated <- collated %>%
            mutate(`Daily change in cumulative total` = if_else(is.na(`Daily change in cumulative total`), 0,
                                                                `Daily change in cumulative total`)) %>%
            mutate(`Cumulative total` = cumsum(`Daily change in cumulative total`))
    }
    
    # Check if cumulative total is monotonically increasing
    mononotic_check <- collated %>%
        arrange(Date) %>%
        mutate(increase = `Cumulative total` - lag(`Cumulative total`)) %>%
        filter(increase < 0)
    if (nrow(mononotic_check) > 0) {
        cat(as.character(mononotic_check$Date), sep = "\n")
        stop("The series doesn't increase monotonically. Check the above dates.")
    }

    # Calculate rates per capita
    collated <- collated %>%
        mutate(`Cumulative total per thousand` = round(1000 * `Cumulative total` / `Population`, 3)) %>%
        mutate(`Daily change in cumulative total per thousand` = round(1000 * `Daily change in cumulative total` / `Population`, 3))

    collated <- collated %>%
        arrange(Date)

    # For each country, if the daily change in the most recent row is less than 50% of the daily
    # change of the day before, the last day is removed from the series. This only applies to the
    # last day of data, so if new data appears and that low daily change remains unchanged,
    # it will not be removed anymore. This means we won’t accidentally remove genuinely low changes.
    last_dailies <- tail(collated$`Daily change in cumulative total`, 2)
    if (all(!is.na(last_dailies)) & (last_dailies[2] < (last_dailies[1] * 0.5))) {
        collated <- head(collated, -1)
    }

    # Remove NA cumulative totals unless all of them are NA
    if (any(!is.na(collated$`Cumulative total`))) {
        collated <- collated %>%
            filter(!is.na(`Cumulative total`))
    }

    # Add number of observations per country
    collated <- collated %>% mutate(`Number of observations` = 1:nrow(collated))

    collated <- add_smoothed_series(collated)

    setDT(collated)

    collated <- merge(collated, confirmed_cases, by = c("Country", "Date"), all.x = TRUE)

    if ("Positive rate" %in% names(collated)) {
        collated$pr_method <- "official"
        setnames(collated, "Positive rate", "Short-term positive rate")
        stopifnot(min(collated$`Short-term positive rate`, na.rm = TRUE) >= 0)
        stopifnot(max(collated$`Short-term positive rate`, na.rm = TRUE) <= 1)
    } else {
        collated$pr_method <- "OWID"
        collated[, `Short-term positive rate` := new_cases_smoothed / `7-day smoothed daily change`]
        collated[`Short-term positive rate` < 0 | `Short-term positive rate` > 1, `Short-term positive rate` := NA]
    }

    # Tests per case = inverse of positive rate
    collated[, `Short-term tests per case` := ifelse(`Short-term positive rate` > 0, round(1 / `Short-term positive rate`, 1), NA_integer_)]
    collated[, `Short-term positive rate` := round(`Short-term positive rate`, 4)]

    # Cumulative versions based on JHU data
    collated[, `Cumulative positive rate` := round(total_cases / `Cumulative total`, 3)]
    collated[`Cumulative positive rate` < 0 | `Cumulative positive rate` > 1, `Cumulative positive rate` := NA]
    collated[, `Cumulative tests per case` := ifelse(`Cumulative positive rate` > 0, round(1 / `Cumulative positive rate`, 1), NA_integer_)]

    collated[, c("total_cases", "new_cases_smoothed") := NULL]

    # Sanity checks
    if (any(collated$`Daily change in cumulative total` == 0, na.rm = TRUE)) {
        View(collated)
        stop("At least one daily change == 0")
    }
    repeated <- collated[, .N, Date][N>1]
    if (nrow(repeated) > 0) {
        View(repeated)
        stop("Duplicate date")
    }
    stopifnot(year(min(collated$Date)) >= 2020)
    stopifnot(max(collated$Date) <= today())

    return(collated)
}

# Process all countries
collated <- lapply(sheet_names, FUN = parse_country)
collated <- rbindlist(collated, use.names = TRUE, fill = TRUE)

# Data corrections
source("testing_data_corrections.R")

# Prepare data for post-processing
collated[, Entity := paste(Country, "-", Units)]
setorder(collated, Country, Units, Date)

# Add ISO codes
add_iso_codes <- function(df) {
    iso <- fread("../../input/iso/iso3166_1_alpha_3_codes.csv")
    setnames(iso, c("ISO code", "Country"))
    stopifnot(all(df$Country %in% iso$Country))
    df <- merge(iso, df, by = "Country")
    return(df)
}
collated <- add_iso_codes(collated)

# Make grapher version
grapher <- collated[, .(
    country = Country,
    date = Date,
    annotation = Units,
    total_tests = `Cumulative total`,
    total_tests_per_thousand = `Cumulative total per thousand`,
    new_tests = `Daily change in cumulative total`,
    new_tests_per_thousand = `Daily change in cumulative total per thousand`,
    new_tests_7day_smoothed = `7-day smoothed daily change`,
    new_tests_per_thousand_7day_smoothed = `7-day smoothed daily change per thousand`,
    cumulative_tests_per_case = `Cumulative tests per case`,
    cumulative_positivity_rate = `Cumulative positive rate`,
    short_term_tests_per_case = `Short-term tests per case`,
    short_term_positivity_rate = `Short-term positive rate`,
    testing_observations = `Number of observations`
)]

# Convert date to fake year format for OWID grapher
grapher[, date := as.integer(difftime(date, origin_date, units = "days"))]
setnames(grapher, c("date", "country"), c("Year", "Country"))

copy_paste_annotation <- unique(grapher[!is.na(annotation), .(Country, annotation)])
copy_paste_annotation <- paste(copy_paste_annotation$Country, copy_paste_annotation$annotation, sep = ": ")
writeLines(copy_paste_annotation, "../../output/testing/grapher_annotations.txt")

# Write grapher file
fwrite(grapher, "../../grapher/COVID testing time series data.csv")

# Make public version
public <- copy(collated)
public[, c("Country", "Units", "Population") := NULL]
public_latest <- merge(public, metadata, all.x = TRUE)
public_latest[, c("Sheet", "Ready for review", "Collate") := NULL]
setorder(public_latest, Entity, -Date)
public_latest <- public_latest[, .SD[1], Entity]
public[, c("Sheet", "Number of observations", "Cumulative tests per case", "Cumulative positive rate", "pr_method") := NULL]
setcolorder(public, "Entity")

# Generate HTML code for WordPress
source("generate_html.R")

# Write public version as Excel file
public_latest <- public_latest[, c(
    "ISO code", "Entity", "Date", "Source URL", "Source label", "Notes",
    "Number of observations", "Cumulative total", "Cumulative total per thousand",
    "Daily change in cumulative total", "Daily change in cumulative total per thousand",
    "7-day smoothed daily change", "7-day smoothed daily change per thousand",
    "Short-term positive rate", "Short-term tests per case",
    "General source label", "General source URL", "Short description", "Detailed description"
)]

fwrite(public_latest, "../../../public/data/testing/covid-testing-latest-data-source-details.csv")
rio::export(public_latest, "../../../public/data/testing/covid-testing-latest-data-source-details.xlsx", overwrite=TRUE)
fwrite(public, "../../../public/data/testing/covid-testing-all-observations.csv")
rio::export(public, "../../../public/data/testing/covid-testing-all-observations.xlsx", overwrite=TRUE)

# Timestamp
ts <- strftime(as.POSIXlt(Sys.time(), "UTC"), "%Y-%m-%dT%H:%M:%S")
writeLines(ts, "../../../public/data/internal/timestamp/owid-covid-data-last-updated-timestamp-test.txt")

# Austria: The definition of the tests in this dataset was changed on 13 January 2021 to include
# both antigen and PCR tests. Because historical testing data was added on that date, the timeline
# cannot be used for continuous calculations. Like most Austrian media outlets and scientific
# institutions, we have therefore changed our test positive rate calculations to only include data
# from February 2021 onwards.
collated[Country == "Austria" & Date < "2021-02-01", `Short-term positive rate` := NA]
collated[Country == "Austria" & Date < "2021-02-01", `Short-term tests per case` := NA]

# Brazil: tests added in batches, creating artificially high PRs
collated[Country == "Brazil", `Short-term positive rate` := NA]
collated[Country == "Brazil", `Short-term tests per case` := NA]

# Ecuador: the PR should start from Sept 2020, because the case data prior to that
# included cases confirmed without PCR tests (while our data only includes PCR tests)
collated[Country == "Ecuador" & Date < "2020-09-14", `Short-term positive rate` := NA]
collated[Country == "Ecuador" & Date < "2020-09-14", `Short-term tests per case` := NA]

# Lebanon: the test definition does not match the case definition (testing figures exclude antigen tests, which can be used to diagnose cases of COVID-19)
collated[Country == "Lebanon", `Short-term positive rate` := NA]
collated[Country == "Lebanon", `Short-term tests per case` := NA]

# Iceland: the test definition does not match the case definition (confirmed cases does not exclude positive results from tests included in the testing figure)
collated[Country == "Iceland", `Short-term positive rate` := NA]
collated[Country == "Iceland", `Short-term tests per case` := NA]

# Qatar: the test definition does not match the case definition (confirmed cases does not exclude positive results from tests included in the testing figure)
collated[Country == "Qatar", `Short-term positive rate` := NA]
collated[Country == "Qatar", `Short-term tests per case` := NA]

# Fiji: estimated positive rate does not match that of the official source
collated[Country == "Fiji", `Short-term positive rate` := NA]
collated[Country == "Fiji", `Short-term tests per case` := NA]

# New Zealand: estimated positive rate does not match that of the official source
collated[Country == "New Zealand", `Short-term positive rate` := NA]
collated[Country == "New Zealand", `Short-term tests per case` := NA]

# Sudden increase in the number of tests due to a backlog
collated[Country == "India" & "2022-04-14" <= Date & Date <= "2022-04-21", `Short-term positive rate` := NA]
collated[Country == "India" & "2022-04-14" <= Date & Date <= "2022-04-21", `Short-term tests per case` := NA]

# North Korea: unclear testing critirea
collated[Country == "North Korea", `Short-term positive rate` := NA]
collated[Country == "North Korea", `Short-term tests per case` := NA]
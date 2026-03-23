activate_links <- function(txt) {
    txt <- str_replace_all(txt, "\\[([^\\]]+)]\\(([^)]+)\\)", '<a href="\\2">\\1</a>')
    return(txt)
}

HTML_CODE <- readLines("input/block_base.html", warn = FALSE) %>% paste0(collapse = "\n")

country_lookup <- fread("../../input/iso/iso3166_1_alpha_3_codes.csv")

html_data <- data.table(public_latest)

html_data[, Country := Entity %>% str_replace(" - .*", "")]

setorder(html_data, Country, `General source label`)

countries <- unique(html_data$Country)

html_add <- function(new_code) {
    HTML_CODE <<- paste0(HTML_CODE, new_code, "\n")
}

index <- sprintf('<p>This is the list of the %s countries for which we have data.<br>You can download the full dataset alongside the detailed source descriptions <a href="https://github.com/owid/covid-19-data/tree/master/public/data/">on GitHub</a>.<br>Or else click to jump to the detailed source description and the latest data for that country:</p>', length(countries))

table_countries <- str_replace_all(str_to_lower(countries), " ", "-")
table_countries <- sprintf('<td><a href="#%s">%s</a></td>', table_countries, countries)
table_countries <- split(table_countries, ceiling(seq_along(table_countries)/4))
table_countries <- sapply(table_countries, FUN = paste0, collapse = "")
table_countries <- paste0("<tr>", table_countries, "</tr>", collapse = "")
table_countries <- sprintf("<table><tbody>%s</tbody></table>", table_countries)

html_add(index)
html_add(table_countries)

for (c in countries) {
    country_rows <- html_data[Country == c]
    html_add(sprintf('<h4>%s</h4>', c))

    ccode <- country_lookup[location == c, iso_code]

    html_add(sprintf('<p style="font-weight:bold; font-style:italic">→ View <a href="https://ourworldindata.org/coronavirus-country-by-country?country=%s">the country profile of %s</a> for the coronavirus pandemic.</p>', ccode, c))

    for (i in 1:nrow(country_rows)) {
        row <- country_rows[i]

        source_number <- ifelse(nrow(country_rows) > 1, sprintf(" #%s", i), "")

        html_add(sprintf('<p><strong>Source%s: </strong><a href="%s">%s</a></p>',
                         source_number,
                         row$`General source URL`,
                         row$`General source label`))

        html_add(sprintf('<p><strong>Short description: </strong>%s</p>',
                         activate_links(row$`Short description`)))

        if (!is.na(row$`Test definition`)) {
            html_add(sprintf('<p><strong>Test definition: </strong>%s</p>', row$`Test definition`))
        }

        if (!is.na(row$`Case definition`)) {
            html_add(sprintf('<p><strong>Case definition: </strong>%s</p>', row$`Case definition`))
        }

        html_add(sprintf('<p><strong>Positive rate: </strong>%s</p>',
                         plyr::mapvalues(row$pr_method, warn_missing = FALSE,
                                         from = c("official", "OWID", NA),
                                         to = c("collected directly from the source. This means that the number of cases that can be deduced based on the number of tests and the positivity rate, is not necessarily equal to the number of cases visible in the rest of our COVID-19 data, which we import from Johns Hopkins University.",
                                         "calculated by Our World in Data as the 7-day rolling average of daily cases, divided by the 7-day rolling average of daily tests.",
                                         "not calculated (see detailed description)."))))

        html_add(sprintf('<p><strong>Detailed description:</strong><br>%s</p>',
                         str_replace_all(activate_links(row$`Detailed description`), "\n", "<br>")))
    }

    html_add("")

}

writeLines(HTML_CODE, "../../output/testing/source_table.html")

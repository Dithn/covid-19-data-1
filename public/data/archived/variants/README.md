# Data on SARS-CoV-2 variants by _Our World in Data_

> For more general information on our COVID-19 data, see our main README file in [`/public/data`](https://github.com/owid/covid-19-data/tree/master/public/data).

Enabled by data from <a href="https://gisaid.org"><img src="https://www.gisaid.org/fileadmin/gisaid/img/schild.png" width="50"/></a>

Our data on SARS-CoV-2 sequencing and variants is sourced from [GISAID](https://gisaid.org), a global science initiative that provides open-access to genomic data of SARS-CoV-2. We recognize the work of the authors and laboratories responsible for producing this data and sharing it via the GISAID initiative.

> Khare, S., et al (2021) GISAID’s Role in Pandemic Response. China CDC Weekly, 3(49): 1049-1051. doi: 10.46234/ccdcw2021.255  PMCID: 8668406
>
> Elbe, S. and Buckland-Merrett, G. (2017) Data, disease and diplomacy: GISAID’s innovative contribution to global health. Global Challenges, 1:33-46. doi:10.1002/gch2.1018  PMCID: 31565258
>
> Shu, Y. and McCauley, J. (2017) GISAID: from vision to reality. EuroSurveillance, 22(13) doi:10.2807/1560-7917.ES.2017.22.13.30494 PMCID: PMC5388101

We download aggregate-level data via [CoVariants.org](https://covariants.org), and we make it available as a [CSV file](covid-variants.csv).


## License

All visualizations, data, and code produced by _Our World in Data_ are completely open access under the [Creative Commons BY license](https://creativecommons.org/licenses/by/4.0/). You have the permission to use, distribute, and reproduce these in any medium, provided the source and authors are credited.

The data produced by third parties and made available by _Our World in Data_ is subject to the license terms from the original third-party authors. We will always indicate the original source of the data in our database, and you should always check the license of any such third-party data before use.


## Fields

| Column field        | Description                                                                  |
|---------------------|------------------------------------------------------------------------------|
| `location`            | Name of the country (or region within a country).                            |
| `date`                | Date of the observation.                                                     |
| `variant`             | Variant name. We use the [WHO label](https://www.who.int/en/activities/tracking-SARS-CoV-2-variants/#Naming-SARS-CoV-2-variants) for Variants of Concern (VoC) and Variants of Interest (VoI), and Pango Lineage for the others. Details on variants included can be found [here](https://covariants.org/variants). |
| `num_sequences`       | Number of sequenced samples that fall into the category `variant`. |
| `perc_sequences`      | Percentage of the sequenced samples that fall into the category `variant`. |
| `num_sequences_total` | Total number of samples sequenced in the last two weeks. |


### Special `variant` values

- `others`: All variants/mutations other than the ones specified (i.e. not listed [in this table](https://covariants.org/variants)).
- `non_who`: All variants/mutations without WHO label.

Note that `non_who` includes `others` and other variants. For instance, variant _B.1.16_ is counted in the `non_who` category but not in `others`, as it does not have a WHO label but is listed [in this table](https://covariants.org/variants).

As a consequence, for a given date, the sum of `perc_sequences` will exceed 1. In order to sum 1, you should exclude `non_who` category.


### Example

|location |date      |variant       |num_sequences|perc_sequences|num_sequences_total|
|---------|----------|--------------|-------------|--------------|-------------------|
|United Kingdom|2021-03-08|B.1.160       |4.0 |0.01 |29598|
|United Kingdom|2021-03-08|B.1.258       |17.0|0.06 |29598|
|United Kingdom|2021-03-08|B.1.221       |3.0 |0.01 |29598|
|United Kingdom|2021-03-08|B.1.1.302     |0.0 |0.0  |29598|
|United Kingdom|2021-03-08|B.1.1.277     |0.0 |0.0  |29598|
|United Kingdom|2021-03-08|B.1.367       |0.0 |0.0  |29598|
|United Kingdom|2021-03-08|B.1.177       |347.0|1.17 |29598|
|United Kingdom|2021-03-08|Beta          |60.0|0.2  |29598|
|United Kingdom|2021-03-08|Alpha         |28772.0|97.21|29598|
|United Kingdom|2021-03-08|Gamma         |6.0 |0.02 |29598|
|United Kingdom|2021-03-08|Delta         |0.0 |0.0  |29598|
|United Kingdom|2021-03-08|Kappa         |12.0|0.04 |29598|
|United Kingdom|2021-03-08|Epsilon       |3.0 |0.01 |29598|
|United Kingdom|2021-03-08|Eta           |97.0|0.33 |29598|
|United Kingdom|2021-03-08|Iota          |1.0 |0.0  |29598|
|United Kingdom|2021-03-08|S:677H.Robin1 |0.0 |0.0  |29598|
|United Kingdom|2021-03-08|S:677P.Pelican|0.0 |0.0  |29598|
|United Kingdom|2021-03-08|others        |276.0|0.93 |29598|
|United Kingdom|2021-03-08|non_who       |647.0|2.19 |29598|

In this extract, we have that during the two weeks prior to 2021-03-08, in the UK, a total of 29598 samples were
sequenced. From these, 28,772 correspond to Alpha variant and 647 are variants without WHO label.

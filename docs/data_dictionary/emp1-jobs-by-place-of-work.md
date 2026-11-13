# EMP1: Jobs by place of work (2023)

**Folder:** `data/DS_RP_TD_EMPLOI_LT_AGEEMPFORM_COMP_2023_CSV_FR/`
**Files:** `..._data.csv` (about 921 MB), `..._metadata.csv` (dictionary)
**Source:** INSEE, census 2023, "Emploi au lieu de travail selon le statut, le temps de travail et l'âge quinquennal" (EMP1)
**Format:** CSV, `;` separator, values in double quotes, UTF-8

## What one row means

The number of jobs (`RP_MEASURE` = `NBEMP`) located in a given geographic area, for one combination of sex, employment form, working time and age group.

## Schema

| Column | Type | Meaning | Values |
| --- | --- | --- | --- |
| `GEO` | text | Code of the geographic unit. Meaning depends on `GEO_OBJECT`. For communes it is the 5-digit INSEE code. | e.g. `"01001"` (for `COM`) |
| `GEO_OBJECT` | text | Geographic level of `GEO` | `FRANCE`, `REG`, `DEP`, `COM`, `ARM`, `EPCI`, `ARR`, `AAV2020`, `UU2020`, `ZE2020`, `BV2022` |
| `SEX` | text | Sex | `F`, `M`, `_T` (total) |
| `EMPFORM` | text | Employment form | `1` non-salaried, `2` salaried, `_T` total |
| `WKTIME` | text | Working time | `FT` full-time, `PT` part-time, `_T` total |
| `AGE` | text | Five-year age group | `Y_LT20` (under 20), `Y20T24` … `Y60T64`, `Y_GE65` (65+), `_T` total |
| `EMPSTA_ENQ` | text | Employment status used by the survey | `1` = employed (actif occupé) |
| `RP_MEASURE` | text | Measure | `NBEMP` = number of jobs (single value in this file) |
| `FREQ` | text | Frequency | `A` = annual (single value) |
| `OBS_STATUS` | text | Observation status | `A` = normal (single value) |
| `TIME_PERIOD` | integer | Year | `2023` (single value) |
| `OBS_VALUE` | float | Number of jobs | Decimal values, because the census figures are estimates |

## Pitfalls

- **The file mixes geographic levels.** The same column holds communes, departments, employment areas and so on. Filter on `GEO_OBJECT == "COM"` to get communes only. Otherwise the same job is counted several times.
- **Totals are included.** `_T` appears in `SEX`, `EMPFORM`, `WKTIME` and `AGE`. Keep one total dimension at a time, or filter to the `_T` rows where you need totals.
- **Jobs, not people.** Each row counts jobs at the workplace. A person with two jobs is counted twice.
- **Read `GEO` as text.** Codes such as `01001` lose their leading zero if parsed as integers.
- **Île-de-France communes** are the codes that start with `75`, `77`, `78`, `91`, `92`, `93`, `94` or `95`. There are 1,266 of them with `GEO_OBJECT == "COM"`.

## Metadata file

`..._metadata.csv` has the columns `COD_VAR;LIB_VAR;COD_MOD;LIB_MOD;GEO_OBJECT`. It lists every variable, its code and its label. Use it to look up any code above. `GEO` has about 41,800 entries.

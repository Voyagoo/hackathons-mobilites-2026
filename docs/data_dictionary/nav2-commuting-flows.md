# NAV2A and NAV2B: Commuting flows by transport mode (2023)

**Folder:** `data/DS_RP_TD_NAVETTES_SEXTRANSPORT_COMP_2023_CSV_FR/`
**Files:** `..._data.csv` (about 688 MB), `..._metadata.csv` (dictionary)
**Source:** INSEE, census 2023, "Déplacements domicile-travail selon le sexe, le lieu de travail et le moyen de transport" (NAV2A and NAV2B)
**Format:** CSV, `;` separator, values in double quotes, UTF-8

## What one row means

The number of employed residents (`RP_MEASURE` = `POP`) who live in the area given by `GEO`, and who work in the place described by `WORK_AREA` or `WORK_URBAN_AREA`, by the transport mode `TRANS`.

**The geography is the residence.** `GEO` is where people live. `WORK_AREA` says where they work, relative to their home commune.

## Schema

| Column | Type | Meaning | Values |
| --- | --- | --- | --- |
| `GEO` | text | Residence code. Meaning depends on `GEO_OBJECT`. For communes it is the 5-digit INSEE code. | e.g. `"01001"` |
| `GEO_OBJECT` | text | Geographic level of `GEO` | Same list as EMP1: `FRANCE`, `REG`, `DEP`, `COM`, `ARM`, `EPCI`, `ARR`, `AAV2020`, `UU2020`, `ZE2020`, `BV2022` |
| `AGE` | text | Age group | `Y_GE15` (15 and over), single value |
| `EMPSTA_ENQ` | text | Employment status | `1` = employed (actif occupé) |
| `WORK_AREA` | text | Workplace relative to the residence commune | `10` same commune, `21` other commune in the same department, `22` other department in the same region, `23` outside the region in metropolitan France, `24T30` other region or abroad, `_T` total |
| `WORK_URBAN_AREA` | text | Urban/rural pattern of residence and workplace | `111` rural residence, same commune of work; `112` urban residence, same commune; `201` rural residence, other commune; `202` urban residence, other commune in the same urban unit; `203` urban residence, work outside the urban unit; `_T` total |
| `SEX` | text | Sex | `M`, `F`, `_T` |
| `TRANS` | text | Transport mode to work | `1` no transport, `2` walking, `3` bicycle, `4` motorised two-wheeler, `5` car/van/lorry, `6` public transport, `_T` total |
| `RP_MEASURE` | text | Measure | `POP` = population (single value) |
| `FREQ` | text | Frequency | `A` = annual (single value) |
| `OBS_STATUS` | text | Observation status | `A` = normal (single value) |
| `TIME_PERIOD` | integer | Year | `2023` (single value) |
| `OBS_VALUE` | float | Number of employed residents | Decimal values, because the census figures are estimates |

## Pitfalls

- **Same mixed-level structure as EMP1.** Filter on `GEO_OBJECT == "COM"` for communes.
- **Several `_T` totals.** `WORK_AREA`, `WORK_URBAN_AREA`, `TRANS` and `SEX` each have a total. Choose one dimension to keep whole, or filter to `_T` on the others.
- **Public transport share.** To compute the share of public transport, divide `TRANS == "6"` by `TRANS == "_T"`, with the other filters fixed at `_T`.
- **Residents, not jobs.** This file counts people by where they live. It cannot be compared with EMP1 without a shared geography.
- **`TRANS = "1"` (no transport)** is labelled "Pas de transport" in the dictionary. Check the metadata before you treat it as "works from home".
- **Read `GEO` as text.** Codes such as `01001` lose their leading zero otherwise.

## Metadata file

`..._metadata.csv` uses the same layout as EMP1 (`COD_VAR;LIB_VAR;COD_MOD;LIB_MOD;GEO_OBJECT`), with the codes listed above.

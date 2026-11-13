# Data dictionary: index

Schema and metadata for each folder in `data/`. Each file describes columns, codes and pitfalls, without the data itself.

| Folder in `data/` | Dictionary file | What it is |
| --- | --- | --- |
| `DS_RP_TD_EMPLOI_LT_AGEEMPFORM_COMP_2023_CSV_FR/` | [emp1-jobs-by-place-of-work.md](emp1-jobs-by-place-of-work.md) | Number of jobs by place of work, 2023 census |
| `DS_RP_TD_NAVETTES_SEXTRANSPORT_COMP_2023_CSV_FR/` | [nav2-commuting-flows.md](nav2-commuting-flows.md) | Employed residents by workplace location and transport mode, 2023 census |
| `ensemble/` | [insee-population-ensemble.md](insee-population-ensemble.md) | Population by administrative unit (commune, canton, department, region) |
| `Communes, cantons et Epci 2025 - Admin Express COG PLUS IGN/` | [ign-admin-express-communes-2025.md](ign-admin-express-communes-2025.md) | Commune, canton and boundary geometries, 2025 |
| `Base_des_zone_d_emploi(composition_communale)/` | [employment-zones-composition.md](employment-zones-composition.md) | Which commune belongs to which employment zone |
| `Base_des_zone_d'emploi_contour/` | [employment-zones-contours.md](employment-zones-contours.md) | Employment zone boundaries |
| `revenu_des_français_a_la_commune/` | [income-by-commune-filosofi.md](income-by-commune-filosofi.md) | Household income indicators by commune |
| `IDFM-gtfs/` | [idfm-gtfs-timetables.md](idfm-gtfs-timetables.md) | Planned public transport timetables, GTFS format |
| `Scheduled_schedules_on_public_transport/` | [idfm-gtfs-timetables.md](idfm-gtfs-timetables.md#pointer-files-not-data) | Pointer files only, not data |

## Common conventions

- Most INSEE and Filosofi CSVs use `;` as separator. The GTFS files use `,`.
- The INSEE census files (EMP1, NAV) are in **long format**: one row per combination of dimensions, with the value in `OBS_VALUE`.
- Commune codes are 5-character INSEE codes with leading zeros (`01001`). Read them as text, not numbers, or the leading zeros are lost.
- Totals are coded `_T`. Summing a dimension that already includes `_T` double-counts.

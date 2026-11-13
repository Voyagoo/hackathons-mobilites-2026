# Employment zones: commune composition (2020)

**Folder:** `data/Base_des_zone_d_emploi(composition_communale)/`
**Files:**

| File | Format | Rows |
| --- | --- | --- |
| `base-des-zones-demploi.csv` | CSV, `;` separator, UTF-8 with BOM | 1,266 Île-de-France communes |
| `base-des-zones-demploi.geojson` | GeoJSON | 1,266 features (commune polygons) |

**Source:** data.iledefrance.fr, "Base des zones d'emploi" (Licence Ouverte).
**Vintage:** zone codes are the 2020 employment zones (ZE2020), as used by INSEE.

## CSV schema

| Column | Meaning | Example |
| --- | --- | --- |
| `Code géo` | 5-digit commune code (join key) | `77016` |
| `Nom de la commune` | Commune name | `Bagneaux-sur-Loing` |
| `Dép` | Department code | `77` |
| `Rég` | Region code (`11` = Île-de-France) | `11` |
| `Geo Shape` | Commune polygon, stored as a JSON string with `coordinates` and `type` | `{"coordinates": [...], "type": "Polygon"}` |
| `Geo Point` | Commune centroid, as `latitude, longitude` with a comma and a space | `48.223313015215105, 2.707509361741183` |
| `Code zone d'emploi` | Employment zone code | `1105` |
| `Zone d'emploi` | Employment zone name | `Fontainebleau-Nemours` |

Note the order in `Geo Point`: latitude first, then longitude. GeoJSON uses longitude first.

## GeoJSON properties

`codgeo` (commune code), `libgeo` (name), `dep`, `reg`, `geo_point_2d` (object with `lon` and `lat`), `ze2020` (zone code), `libze2020` (zone name).

## Pitfalls

- **Commune-level, not zone-level.** One row per commune. To count communes per zone, group by `Code zone d'emploi`.
- **Some department codes are numeric and some are text.** Read `Code géo` and `Dép` as text to keep leading zeros.
- **Geometry is a string in the CSV.** Parse `Geo Shape` with a JSON parser before using it as geometry. Use the GeoJSON file for direct mapping.
- **Île-de-France only.** The file has no communes from other regions, so it is not a national link table.

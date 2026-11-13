# IGN ADMIN-EXPRESS: Communes, cantons and EPCI 2025

**Folder:** `data/Communes, cantons et Epci 2025 - Admin Express COG PLUS IGN/`
**Source:** IGN ADMIN-EXPRESS (COG PLUS, simplified), published on data.gouv.fr
**Files:**

| File | Format | Content |
| --- | --- | --- |
| `a-com2025.geojson` | GeoJSON, about 44 MB | Commune boundaries, all of France |
| `a-com2025-topo.json` | TopoJSON, about 12 MB | Same communes, topology-encoded (smaller) |
| `a-can2025.geojson` | GeoJSON, about 12 MB | Canton boundaries |

## `a-com2025.geojson`

- **Geometry:** `MultiPolygon`, one feature per commune. About 34,900 features, covering all of France, not only Île-de-France.
- **CRS:** no explicit `crs` member. GeoJSON defaults to WGS 84 (longitude, latitude).
- **Properties:**

| Property | Type | Meaning | Example |
| --- | --- | --- | --- |
| `codgeo` | text | 5-digit INSEE commune code (join key) | `"01001"` |
| `libgeo` | text | Commune name | `"L'Abergement-Clémenciat"` |
| `population` | integer | Population, from IGN's own source. It may not match the INSEE file in `ensemble/`. | `859` |
| `can` | text | Canton code | `"0108"` |
| `dept` | text | Department code | `"01"` |
| `reg` | text | Region code. `"11"` = Île-de-France. | `"84"` |
| `superf` | number | Area. The unit is probably hectares. Check the IGN documentation before using it. | `1590` |

## `a-com2025-topo.json`

TopoJSON version of the same communes. Read with a TopoJSON reader, not as plain GeoJSON. Use it when file size matters. Geopandas can read the GeoJSON file directly.

## `a-can2025.geojson`

Canton boundaries, with the same kind of properties as the commune file (canton code, department, region).

## Pitfalls

- **All of France.** Filter on `reg == "11"` to get Île-de-France.
- **`population` is not the INSEE count.** Use `ensemble/donnees_communes.csv` for the official population, and join it on `codgeo` = `COM`.
- **Join on text codes.** `codgeo` is text. Converting it to a number removes the leading zero and breaks the join.
- **Boundaries and codes are from 2025.** The commune codes in the 2023 census files may differ if a commune merged or split since then. Check the COG (code officiel géographique) history before you join on old codes.

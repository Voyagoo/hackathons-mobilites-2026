# Employment zones: boundaries (2020)

**Folder:** `data/Base_des_zone_d'emploi_contour/`
**Files:**

| File | Format | Rows |
| --- | --- | --- |
| `base-des-zones-demploi-contours.geojson` | GeoJSON | 15 features (one per employment zone) |
| `base-des-zones-demploi-contours.csv` | CSV, `;` separator, UTF-8 | One row per zone |

**Source:** data.iledefrance.fr, "Base des zones d'emploi, contours" (Licence Ouverte).
**Vintage:** 2020 employment zones (ZE2020).

## GeoJSON properties

| Property | Meaning | Example |
| --- | --- | --- |
| `ze2020` | Employment zone code | `1101` |
| `libze2020` | Employment zone name | `Cergy-Vexin` |
| `nb_com` | Number of communes in the zone (stored as text) | `"120"` |
| `geo_point_2d` | Centroid, object with `lon` and `lat` | `{"lon": 2.005, "lat": 49.099}` |

The geometry is a `Polygon` or `MultiPolygon` in longitude, latitude order. No CRS is declared, so assume WGS 84.

## CSV schema

| Column | Meaning |
| --- | --- |
| `Geo Shape` | Polygon as a JSON string |
| `Geo Point` | Centroid, `latitude, longitude` |
| `Code zone d'emploi` | Zone code |
| `Zone d'emploi` | Zone name |
| `Communes` | List of the communes in the zone |

## Pitfalls

- **15 zones.** The composition file (previous folder) has 1,266 communes, which is the commune count, not the zone count. Do not confuse the two.
- **`nb_com` is text.** Convert to integer before summing.
- **Boundaries are simplified.** The contours may not match commune polygons exactly. Do not use them to decide which commune a point belongs to. Use the composition file for that.

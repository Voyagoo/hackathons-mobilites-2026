# INSEE population, all administrative units (`ensemble/`)

**Folder:** `data/ensemble/`
**Source:** INSEE, "Populations de référence" (formerly "populations légales"), full file. The page is linked from the INSEE statistics site.
**Format:** CSV, `;` separator, UTF-8 (`metadonnees.csv` also `;`)

The folder has one dictionary file and seven data files, one per level of geography. The data files share the same population columns.

## Files

| File | Rows of geography | Key columns |
| --- | --- | --- |
| `metadonnees.csv` | Dictionary (about 39,100 lines) | Variable and code labels for all the `donnees_*.csv` files |
| `donnees_communes.csv` | Communes (about 35,000) | `COM`, `Commune`, `DEP`, `REG`, `PMUN`, `PCAP`, `PTOT` |
| `donnees_communes_deleguees.csv` | Communes déléguées (former communes that now belong to a larger commune) | `COMP`, `Commune pôle`, `COM`, `Commune`, `PMUN`, `PCAP`, `PTOT` |
| `donnees_arrondissements.csv` | Arrondissements | `CODARR`, `ARR`, `Arrondissement`, `NBCOM`, `PMUN`, `PTOT` |
| `donnees_cantons.csv` | Cantons | `CODCAN`, `CAN`, `Canton`, `NBCOM`, `PMUN`, `PTOT` |
| `donnees_fractions_cantonales.csv` | Canton fractions (for communes divided between cantons) | `CODCOM`, `Commune`, `CODFRAC_CAN`, `FRAC_CAN`, `Fraction cantonale`, `PMUN`, `PCAP`, `PTOT` |
| `donnees_departements.csv` | Departments | `DEP`, `Département`, `NBARR`, `NBCAN`, `NBCOM`, `PMUN`, `PTOT` |
| `donnees_regions.csv` | Regions | `REG`, `Région`, `NBARR`, `NBCAN`, `NBCOM`, `PMUN`, `PTOT` |
| `donnees_collectivites.csv` | Overseas collectivities | `COL`, `Collectivité`, `CODCOM`, `COM`, `Commune`, `PMUN`, `PCAP`, `PTOT` |

## Population columns

These are the standard INSEE names, not explained in the files themselves. Confirm the definitions in `metadonnees.csv` or the INSEE page.

| Column | Meaning |
| --- | --- |
| `PMUN` | Municipal population |
| `PCAP` | Population counted separately (for example, students in a different commune) |
| `PTOT` | Total population = `PMUN` + `PCAP` |
| `NBCOM`, `NBARR`, `NBCAN` | Number of communes, arrondissements or cantons inside the unit |

## Key columns

| Column | Meaning |
| --- | --- |
| `REG`, `DEP`, `CODARR`, `CODCAN`, `CODCOM` | Codes of the parent units. Keep them as text. |
| `COM` | 5-digit INSEE commune code (for example `01001`). Join key to the other files. |
| `Commune`, `Région`, `Département` | Labels |

Sample row in `donnees_communes.csv`: `REG=84`, `DEP=01`, `COM=01001`, `Commune=L'Abergement-Clémenciat`, `PMUN=860`, `PCAP=16`, `PTOT=876`.

## Pitfalls

- **Codes are text.** `DEP` `01` and `REG` `01` are different things, and both lose their leading zeros as numbers.
- **Overseas regions and collectivities** appear in the same files. Filter on `REG == "11"` for Île-de-France.
- **Communes déléguées** are part of a commune. Do not add them to `donnees_communes.csv` or the total is counted twice.
- **Population is the vintage in the file's name and source page.** Do not compare it with the 2025 boundaries without checking the year.

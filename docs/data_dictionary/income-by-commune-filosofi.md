# Income by commune, Filosofi (`revenu_des_français_a_la_commune/`)

**File:** `revenu-des-francais-a-la-commune-1765372688826.csv` (about 5 MB, about 34,900 rows)
**Source:** INSEE, Filosofi (fiscal and social income, by commune), distributed on data.gouv.fr (Licence Ouverte).
**Format:** CSV, `;` separator, UTF-8, 57 columns, header in French.

## One row means

One commune (or Paris arrondissement or other sub-unit listed by INSEE), with income statistics for its fiscal households.

## Identifier columns

| Column | Meaning | Example |
| --- | --- | --- |
| `Nom géographique GMS` | Geographic name with the level prefix | `L'Abergement-Clémenciat` |
| `Code géographique` | 5-digit INSEE code (join key) | `01001` |
| `Libellé géographique` | Commune name | `L'Abergement-Clémenciat` |

## Value columns

The header has two blocks, marked by a prefix on each column:

- **`[DISP]`**: available income, the disposable income per consumption unit (after tax and transfers). INSEE's usual convention. Confirm in the INSEE Filosofi documentation.
- **`[DEC]`**: declared income, before some adjustments. Also INSEE's convention. Confirm in the documentation.

Columns in each block (names as they appear, abbreviated):

| Group | Columns |
| --- | --- |
| Counts | Number of fiscal households, number of persons, number of consumption units |
| Income levels (€) | 1st quartile, median, 3rd quartile, interquartile range, deciles 1, 2, 3, 4, 6, 7, 8, 9 |
| Inequality | Decile ratio D9/D1, S80/S20, Gini index |
| Income composition (%) | Share of employment income (wages, unemployment benefits, self-employment income), pensions, property income, social benefits (family, minimum social benefits, housing), taxes |
| Taxation (`[DEC]` only) | Share of fiscal households that pay income tax |

The `[DEC]` block repeats the same measures with the declared-income definition.

## Pitfalls

- **Missing values are common.** Small communes have empty cells, because INSEE hides values that would identify a household (statistical secrecy). Count the blanks before you rely on a column.
- **Two columns are named "Nbre de ménages fiscaux".** One is in `[DISP]` and one is in `[DEC]`. Use the column position or the prefix to tell them apart.
- **Decimal separator.** Values use a dot, so they are safe to read as float without changing the locale.
- **Île-de-France rows.** Filtering on codes that start with `75`, `77`, `78`, `91`–`95` gives about 1,287 rows. This is slightly more than the 1,266 communes in the employment-zone files, because it includes Paris arrondissements and other sub-units. Check the level before you join.
- **Column names contain special characters** such as `ᵉʳ`, `’` and non-breaking spaces. Rename them to plain names before using them in code.

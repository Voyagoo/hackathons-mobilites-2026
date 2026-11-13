# Validation of the travel times

Checked on 13 Nov 2026 against the final matrices (`data/processed/ttm/`). Settings: Paris split into arrondissements, routing from each area's busiest station, transit departures in the hour around the stated time, 25th percentile. Transit is the weekday 08:30 scenario; car is free-flow.

"Expected" is a rough station-to-station range for a typical journey planner result.

| From (station) | To (station) | Transit (min) | Car (min) | Expected transit | Check |
| --- | --- | --- | --- | --- | --- |
| Paris 8e (Saint-Lazare) | Versailles (Chantiers) | 44 | 31 | 30–45 | ok |
| Paris 10e (Gare du Nord) | Saint-Denis | 12 | 17 | 10–25 | ok |
| Paris 8e (Saint-Lazare) | Courbevoie (Pont de Neuilly) | 30 | 15 | 15–30 | ok |
| Paris 8e (Saint-Lazare) | Cergy (Préfecture) | 48 | 35 | 40–60 | ok |
| Paris 12e (Gare de Lyon) | Créteil (Pointe du Lac) | 35 | 23 | 25–45 | ok |
| Paris 12e (Gare de Lyon) | Évry-Courcouronnes | 53 | 35 | 35–55 | ok |
| Paris 10e (Gare du Nord) | Meaux | 56 | 45 | 30–50 | slow: Meaux trains leave from Gare de l'Est, not the 10e anchor |
| Paris 12e (Gare de Lyon) | Melun | 50 | 50 | 30–50 | ok |
| Paris 10e (Gare du Nord) | CDG airport (Tremblay) | 39 | 29 | 30–50 | ok |
| Paris 1er (Louvre) | Paris 15e (Montparnasse) | 22 | 20 | 10–25 | ok |
| Paris 20e (Porte des Lilas) | Paris 16e (Porte de Saint-Cloud) | 45 | 27 | 30–50 | ok |
| Cergy (Préfecture) | Pontoise | 15 | 9 | 5–20 | ok |
| Versailles (Chantiers) | Guyancourt | 32 | 15 | 15–35 | ok |
| Saint-Denis | Montreuil (Mairie) | 38 | 24 | 30–55 | ok |
| Créteil (Pointe du Lac) | Versailles (Chantiers) | 74 | 29 | 60–90 | ok |

14 of 15 trips fall in the expected range. No trip is implausibly fast.

## What changed to get here

1. **Commune centroids → busiest station.** With geometric centroids, Versailles started in the château park and Roissy in the airport; transit times were 20–30 minutes too long.
2. **One point for Paris → 20 arrondissements.** With Paris as one station (Saint-Lazare), every trip to the east or south first crossed Paris: Paris → Saint-Denis went from 28 to 13 minutes, Paris → CDG from 55 to 40.
3. **30-minute window with the median → one-hour window with the 25th percentile.** Mormant has trains at 08:25 and 09:25. Every departure between 08:30 and 09:00 had just missed the train, so Nangis (8 minutes by train) came out at 49 minutes and Paris was beyond 90. Now: Nangis 24, Paris 10e 63, and Mormant reaches 117 areas within 90 minutes instead of 27.

4. **Unreachable routing points → nearest usable stop.** For six areas the busiest station is not connected to the walking network in the map data, so public transport reached nothing from it, and nobody reached its jobs. This included Paris 17e (Neuilly - Porte Maillot, 110,000 jobs) and Chessy (Marne-la-Vallée - Chessy). `pipeline/fix_unroutable_anchors.py` moved both to the nearest stop that routes; Paris 17e went from 1.8% to 63% of jobs within 45 minutes at the peak. Four small rural communes (Beaumont-du-Gâtinais, Villiers-Saint-Georges, Louan-Villegruis-Fontaine, Melz-sur-Seine) have no usable stop and are shown as "no route found". The car matrix was not recomputed for the two moved points.

## Known remaining biases

- The Marne-la-Vallée - Chessy RER station itself cannot be reached on foot in the network, so access around it is understated.

- Routing from the main station favours transit for residents who live far from it.
- The 25th percentile assumes travellers roughly time their departure; someone arriving at random waits longer on infrequent lines.
- Car times have no congestion, so the car benchmark is optimistic, especially at 08:30.
- Some anchors are at the edge of their commune (Créteil: Pointe du Lac, metro terminus; Roissy-en-France: the airport cargo area, where most of its jobs are).

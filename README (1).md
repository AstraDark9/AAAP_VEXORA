# TRACE
### Crime Intelligence & Prediction Platform

A crime-data explorer for India, presented as a detective's case board rather than a dashboard. A Flask + scikit-learn API serves a ~40,000-row incident dataset; a React frontend lays it out as four "exhibits" — a heatmap, a prediction model, a city-vs-city comparison, and a log of real cases per crime type.

## Overview

| Exhibit | Page | Route | What it does |
|---|---|---|---|
| A | The Map | `/heatmap` | Leaflet heatmap of a selected crime type across Indian cities |
| B | The Verdict | `/ml` | RandomForest model predicts which cities a crime type is most likely to recur in |
| C | Cross-Examination | `/compare` | Line chart comparing two cities' year-over-year counts for a crime |
| D | The Dossier | `/dossier` | Curated real-world cases on record for each crime type |

`JudgementLanding.jsx` is the landing page (`/`) that ties the exhibits together.

## Tech stack

**Backend** — Flask, Flask-CORS, pandas, numpy, scikit-learn (`RandomForestClassifier`), gunicorn.

**Frontend** — React 19 + Vite, react-router-dom, Chart.js / react-chartjs-2, Leaflet / react-leaflet / leaflet.heat, lucide-react, motion.

## Project structure

```
Judgement/
├── app.py                    # Flask API + legacy Jinja routes
├── requirements.txt
├── crime_dataset_india.csv   # ~40,290-row dataset
├── aa.py                     # scratch script: prints unique crimes/cities
├── bb.py                     # scratch script: geocodes cities into cityCoords.js (needs geopy)
├── templates/, static/       # legacy server-rendered pages, superseded by frontend-react
└── frontend-react/
    ├── package.json
    ├── vite.config.js
    ├── public/india.geojson
    └── src/
        ├── App.jsx               # route table
        ├── JudgementLanding.jsx  # landing / evidence board
        ├── Heatmap.jsx           # Exhibit A
        ├── ML.jsx                # Exhibit B
        ├── Compare.jsx           # Exhibit C
        ├── TheDossier.jsx        # Exhibit D
        ├── crimeCases.js         # case data behind the Dossier
        ├── cityCoords.js         # lat/lon lookup for the heatmap
        └── components/DecryptedText.jsx
```

## Getting started

You need two servers running side by side: the Flask API and the Vite dev server.

### 1. Backend

```bash
cd Judgement
pip install -r requirements.txt
python app.py
```

Starts on `http://127.0.0.1:5000`. On boot it loads `crime_dataset_india.csv` and trains the RandomForest model in memory — there's no saved model file, so this happens fresh on every restart and takes a moment.

### 2. Frontend

```bash
cd Judgement/frontend-react
npm install
npm run dev
```

Starts on Vite's default port (`http://localhost:5173`). Most pages call the API directly at `http://127.0.0.1:5000` — there's no `.env` or dev proxy, so if you move the backend off that host/port you'll need to update the fetch calls (see Known gaps below).

## API reference

| Method | Route | Returns |
|---|---|---|
| `GET` | `/crimes` | Sorted list of distinct crime descriptions |
| `GET` | `/cities` | Sorted list of distinct cities |
| `GET` | `/crime/<crime>` | Per-city raw + normalized counts, and 2020–2024 yearly counts (feeds the heatmap) |
| `GET` | `/ml_data/<crime>` | Per-city raw + normalized counts, and by-year counts (feeds the Verdict chart) |
| `GET` | `/predict/<crime>` | Cities ranked by the RandomForest's predicted probability for that crime |
| `GET` | `/compare_data/<crime>/<city1>/<city2>` | Year-by-year counts for two cities (feeds Cross-Examination) |

`app.py` also still serves `/`, `/index`, `/ml`, and `/compare` as server-rendered Jinja templates from `templates/`. Those predate the React app and aren't linked from it — treat them as legacy.

## Dataset

`crime_dataset_india.csv` — around 40,290 reported incidents. Columns: `Report Number`, `Date Reported`, `Date of Occurrence`, `Time of Occurrence`, `City`, `Crime Code`, `Crime Description`, `Victim Age`, `Victim Gender`, `Weapon Used`, `Crime Domain`, `Police Deployed`, `Case Closed`, `Date Case Closed`.

The model is trained on `City`, `Crime Description`, `Year`, and `Victim Age` (label-encoded) to predict `Crime Domain`.

## Design system

The frontend shares one visual language across pages — a detective's evidence board, not a SaaS dashboard.

- **Palette** — near-black ground (`#000`), evidence-red (`#a8201a`), brass (`#ab8756`), slate (`#4a5a68`), parchment cards (`#efe7d2` → `#e3d8b9`) with ink text (`#2a2419`).
- **Type** — Fraunces (serif) for headlines, IBM Plex Mono for everything else — labels, body copy, data.
- **Motifs** — pinned/tilted parchment cards, brass pins, hand-drawn connecting strings, film-grain texture, a live "incidents logged" ticker, and `DecryptedText` for glitch-style text reveals.

`Compare.jsx` (Exhibit C) is the most recently restyled page and is a good reference for the token values in code.

## Known gaps

- **Hardcoded API host** — most pages fetch `http://127.0.0.1:5000` directly; nothing reads from an env variable, so deploying frontend and backend separately will need a config pass.
- **Inconsistent fetch paths** — `TheDossier.jsx` calls the relative path `/crimes` instead of the full backend URL the other pages use, so in dev it silently falls back to its bundled `crimeCases.js` data rather than hitting Flask. Worth aligning.
- **No persisted model** — `RandomForestClassifier` retrains from the CSV on every backend start; there's no `.pkl` or similar being saved/loaded.
- **`bb.py` needs `geopy`**, which isn't listed in `requirements.txt`. It's a one-off script used to generate `cityCoords.js`, not part of the running app.
- **Legacy `templates/` and `static/`** duplicate functionality now handled by `frontend-react` and could likely be removed once nothing depends on them.

## License

Hackathon prototype — not currently licensed for reuse.

import pandas as pd
import numpy as np

from flask import Flask, render_template, jsonify
from flask_cors import CORS

from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier


# --------------------------------------------------
# APP SETUP
# --------------------------------------------------

app = Flask(__name__)
CORS(app)


# --------------------------------------------------
# LOAD DATASET
# --------------------------------------------------

df = pd.read_csv("crime_dataset_india.csv")

print("Dataset loaded")
print("Columns:")
print(df.columns.tolist())

print("\nCrime types:")
print(df["Crime Description"].dropna().unique())


# --------------------------------------------------
# DATA PREPROCESSING
# --------------------------------------------------

df["Date of Occurrence"] = pd.to_datetime(
    df["Date of Occurrence"],
    errors="coerce"
)

df["Victim Age"] = df["Victim Age"].fillna(
    df["Victim Age"].median()
)

df["Year"] = df["Date of Occurrence"].dt.year


# --------------------------------------------------
# ENCODING FOR ML
# --------------------------------------------------

le_city = LabelEncoder()
le_crime = LabelEncoder()

df["City_enc"] = le_city.fit_transform(df["City"])
df["Crime_enc"] = le_crime.fit_transform(
    df["Crime Description"]
)


# --------------------------------------------------
# RANDOM FOREST MODEL
# --------------------------------------------------

X = df[
    [
        "City_enc",
        "Crime_enc",
        "Year",
        "Victim Age"
    ]
]

y = df["Crime Domain"]

model = RandomForestClassifier(
    random_state=42
)

model.fit(X, y)


# --------------------------------------------------
# GET AVAILABLE CRIMES
# --------------------------------------------------

@app.route("/crimes")
def crimes():

    crimes = sorted(
        df["Crime Description"]
        .dropna()
        .unique()
        .tolist()
    )

    return jsonify(crimes)


# --------------------------------------------------
# HEATMAP DATA
# --------------------------------------------------

@app.route("/crime/<crime>")
def crime_data(crime):

    print("Requested crime:", crime)

    # Exact match
    filtered = df[
        df["Crime Description"] == crime
    ].copy()

    print("Matching rows:", len(filtered))

    # -----------------------------
    # CITY COUNTS
    # -----------------------------

    crime_counts = (
        filtered["City"]
        .value_counts()
        .to_dict()
    )

    max_val = (
        max(crime_counts.values())
        if crime_counts
        else 0
    )

    if max_val == 0:

        normalized = {}

    else:

        normalized = {
            city: count / max_val
            for city, count in crime_counts.items()
        }


    # -----------------------------
    # YEARLY COUNTS
    # -----------------------------

    filtered["Year"] = pd.to_datetime(
        filtered["Date of Occurrence"],
        errors="coerce"
    ).dt.year

    yearly_counts = (
        filtered["Year"]
        .value_counts()
        .sort_index()
        .reindex(
            [2020, 2021, 2022, 2023, 2024],
            fill_value=0
        )
        .to_dict()
    )


    # -----------------------------
    # RESPONSE
    # -----------------------------

    return jsonify({
        "crime": crime,
        "normalized": normalized,
        "raw": crime_counts,
        "yearly": yearly_counts
    })


# --------------------------------------------------
# ML DATA
# --------------------------------------------------

@app.route("/ml_data/<crime>")
def ml_data(crime):

    filtered = df[
        df["Crime Description"] == crime
    ].copy()

    raw_counts = (
        filtered["City"]
        .value_counts()
        .to_dict()
    )

    max_val = (
        max(raw_counts.values())
        if raw_counts
        else 0
    )

    normalized = {
        city: count / max_val
        if max_val
        else 0
        for city, count
        in raw_counts.items()
    }

    filtered["Year"] = pd.to_datetime(
        filtered["Date Reported"],
        format="%d-%m-%Y %H:%M",
        errors="coerce"
    ).dt.year

    by_year = (
        filtered
        .groupby("Year")
        .size()
        .to_dict()
    )

    return jsonify({
        "normalized": normalized,
        "raw": raw_counts,
        "byYear": by_year
    })


# --------------------------------------------------
# PREDICTION
# --------------------------------------------------

@app.route("/predict/<crime>")
def predict(crime):

    # Check whether crime exists
    if crime not in le_crime.classes_:
        return jsonify({
            "error": f"Unknown crime: {crime}"
        }), 404

    crime_id = le_crime.transform(
        [crime]
    )[0]

    cities = df["City"].unique()

    predictions = {}

    for city in cities:

        city_id = le_city.transform(
            [city]
        )[0]

        sample = [
            [
                city_id,
                crime_id,
                2025,
                30
            ]
        ]

        prob = model.predict_proba(
            sample
        ).max()

        predictions[city] = float(prob)


    top = dict(
        sorted(
            predictions.items(),
            key=lambda x: x[1],
            reverse=True
        )
    )

    return jsonify(top)


# --------------------------------------------------
# OLD FLASK HTML ROUTES
# --------------------------------------------------

@app.route("/")
def landing():

    return render_template(
        "index2.html"
    )


@app.route("/index")
def heatmap_page():

    crimes = (
        df["Crime Description"]
        .dropna()
        .unique()
        .tolist()
    )

    return render_template(
        "index.html",
        crimes=crimes
    )

@app.route("/cities")
def cities():
    cities = sorted(df["City"].dropna().unique().tolist())
    return jsonify(cities)

@app.route("/ml")
@app.route("/ml/<crime>")
def ml_page(crime=None):

    crimes = (
        df["Crime Description"]
        .dropna()
        .unique()
        .tolist()
    )

    return render_template(
        "ml.html",
        crimes=crimes,
        selected_crime=crime
    )


@app.route("/compare")
def compare_page():

    crimes = (
        df["Crime Description"]
        .dropna()
        .unique()
        .tolist()
    )

    cities = (
        df["City"]
        .dropna()
        .unique()
        .tolist()
    )

    return render_template(
        "compare.html",
        crimes=crimes,
        cities=cities
    )


# --------------------------------------------------
# COMPARE DATA
# --------------------------------------------------

@app.route(
    "/compare_data/<crime>/<city1>/<city2>"
)
def compare_data(crime, city1, city2):

    filtered = df[
        df["Crime Description"] == crime
    ].copy()

    filtered["Year"] = pd.to_datetime(
        filtered["Date Reported"],
        format="%d-%m-%Y %H:%M",
        errors="coerce"
    ).dt.year

    city1_counts = (
        filtered[
            filtered["City"] == city1
        ]
        .groupby("Year")
        .size()
        .to_dict()
    )

    city2_counts = (
        filtered[
            filtered["City"] == city2
        ]
        .groupby("Year")
        .size()
        .to_dict()
    )

    return jsonify({
        "years": sorted(
            list(
                set(city1_counts.keys())
                .union(
                    set(city2_counts.keys())
                )
            )
        ),
        "city1": city1_counts,
        "city2": city2_counts
    })


# --------------------------------------------------
# START SERVER
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5000
    )
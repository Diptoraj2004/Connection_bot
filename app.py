import pandas as pd
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load databases
df_psy = pd.read_csv("psychologists.csv")
df_ngos = pd.read_csv("ngos.csv")

def search_nearby(df, city, state):
    # Match by city or state
    results = df[(df['city'].str.lower() == city.lower()) |
                 (df['state'].str.lower() == state.lower())]
    return results.to_dict(orient="records")

@app.route("/escalate", methods=["POST"])
def escalate():
    data = request.json
    days = data.get("days", 0)
    improvement = data.get("improvement", True)
    city = data.get("city", "")
    state = data.get("state", "")

    if not improvement and days >= 7:
        psy_matches = search_nearby(df_psy, city, state)
        ngo_matches = search_nearby(df_ngos, city, state)
        return jsonify({
            "status": "escalated",
            "psychologists": psy_matches,
            "ngos": ngo_matches
        })
    else:
        return jsonify({"status": "monitoring", "message": "Continue support"})

if __name__ == "__main__":
    app.run(debug=True)

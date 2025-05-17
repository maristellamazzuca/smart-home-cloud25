from flask import Flask, request, render_template
from google.cloud import firestore
import anomaly_predictor
import os

app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')
db = firestore.Client()

@app.route("/receive_data", methods=["POST"])
def receive_data():
    try:
        data = request.get_json()
        print(f"[DEBUG] Ricevuto: {data}")

        if not data or "timestamp" not in data or "use [kW]" not in data:
            return "Dati incompleti", 400

        timestamp = data["timestamp"]
        doc_ref = db.collection("sensors").document("sensor1")
        if doc_ref.get().exists():
            doc_ref.update({"data": firestore.ArrayUnion([data])})
        else:
            doc_ref.set({"data": [data]})

        try:
            current_value = float(data["use [kW]"])
            result, triggered = anomaly_predictor.predict_and_alert(current_value, timestamp)
            print("[DEBUG] Risultato:", result, "Triggered:", triggered)
        except Exception as e:
            print("[ERROR] Errore predizione:", e)
            return f"Errore predizione: {str(e)}", 500

        return "Dati salvati" + (" con anomalia" if triggered else ""), 200

    except Exception as e:
        print("[ERROR] Errore generale:", e)
        return f"Errore generale: {str(e)}", 500

@app.route("/view_data", methods=["GET"])
def view_data():
    try:
        doc = db.collection("sensors").document("sensor1").get()
        if not doc.exists():
            return render_template("view_data.html", data=[], headers=[])
        data = doc.to_dict().get("data", [])
        headers = sorted(set().union(*(d.keys() for d in data if isinstance(d, dict))))
        return render_template("view_data.html", data=data, headers=headers)
    except Exception as e:
        return f"Errore view_data: {str(e)}", 500

@app.route("/view_anomalies", methods=["GET"])
def view_anomalies():
    try:
        doc = db.collection("anomalies").document("log").get()
        if not doc.exists():
            return render_template("anomalies.html", anomalies=[])
        raw = doc.to_dict().get("events", [])
        anomalies = [a for a in raw if isinstance(a, dict)]
        anomalies = sorted(anomalies, key=lambda x: x.get("timestamp", ""))
        return render_template("anomalies.html", anomalies=anomalies)
    except Exception as e:
        print("[ERROR] view_anomalies:", e)
        return f"Errore anomalies: {str(e)}", 500

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, render_template
from google.cloud import firestore
import anomaly_predictor
import os

app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')
db = firestore.Client()

@app.route("/receive_data", methods=["POST"])
def receive_data():
    return process_data(request, "Parte 1")

@app.route("/receive_data_cf", methods=["POST"])
def receive_data_cf():
    return process_data(request, "Parte 2")

def process_data(request, parte):
    try:
        data = request.get_json()
        print(f"[DEBUG] Richiesta ricevuta in {parte}: {data}")

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
            print(f"[DEBUG] Risultato predizione: {result}, triggered: {triggered}")
        except Exception as e:
            print("[ERROR] durante predict_and_alert:", e)
            return f"Errore interno (predict): {str(e)}", 500

        return "Dati salvati" + (" con anomalia" if triggered else ""), 200

    except Exception as e:
        print("[ERROR] Generale in process_data:", e)
        return f"Errore interno: {str(e)}", 500

@app.route("/view_data", methods=["GET"])
def view_data():
    try:
        doc = db.collection("sensors").document("sensor1").get()
        if not doc.exists():
            return render_template("view_data.html", data=[], headers=[])

        data_list = doc.to_dict().get("data", [])
        data_list = sorted(data_list, key=lambda x: x.get("timestamp", ""))
        headers = sorted(set().union(*(d.keys() for d in data_list if isinstance(d, dict))))
        return render_template("view_data.html", data=data_list, headers=headers)

    except Exception as e:
        return f"Errore durante la lettura dei dati: {str(e)}", 500

@app.route("/view_anomalies", methods=["GET"])
def view_anomalies():
    try:
        doc = db.collection("anomalies").document("log").get()
        if not doc.exists():
            return render_template("anomalies.html", anomalies=[])

        raw = doc.to_dict().get("events", [])

        # Filtro di sicurezza
        anomalies = [a for a in raw if isinstance(a, dict) and "timestamp" in a]
        anomalies = sorted(anomalies, key=lambda x: x["timestamp"])

        return render_template("anomalies.html", anomalies=anomalies)

    except Exception as e:
        print("[ERROR] in view_anomalies:", e)
        return f"Errore durante la visualizzazione delle anomalie: {str(e)}", 500

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

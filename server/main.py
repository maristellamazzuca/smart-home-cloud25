from flask import Flask, request, render_template
from google.cloud import firestore
import anomaly_predictor
import os

# Inizializzazione Flask e Firestore
app = Flask(__name__)
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')
db = firestore.Client()

print("Tipo di predict_and_alert:", type(anomaly_predictor.predict_and_alert))

# === Parte 1: ricezione dati dal client (simula invio da sensore IoT)
@app.route("/receive_data", methods=["POST"])
def receive_data():
    return process_data(request, "Parte 1")

# === Parte 2: ricezione da Cloud Function (stesso meccanismo, ma separato)
@app.route("/receive_data_cf", methods=["POST"])
def receive_data_cf():
    return process_data(request, "Parte 2")

# === Funzione centrale: salva i dati, richiama la Parte 4 per la predizione
def process_data(request, parte):
    try:
        data = request.get_json()
        print(f"[DEBUG] Richiesta ricevuta in {parte}: {data}")

        if not data or "timestamp" not in data or "use [kW]" not in data:
            print("[ERROR] Dati incompleti")
            return "Dati incompleti", 400

        timestamp = data.get("timestamp")
        doc_ref = db.collection("sensors").document("sensor1")

        if doc_ref.get().exists():
            doc_ref.update({"data": firestore.ArrayUnion([data])})
        else:
            doc_ref.set({"data": [data]})

        # === Parte 4: predizione e rilevamento anomalia
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

# === Parte 3: visualizzazione dei dati raccolti
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
        print("[ERROR] in view_data:", e)
        return f"Errore durante la lettura dei dati: {str(e)}", 500

# === Parte 4b: visualizzazione delle anomalie rilevate
@app.route("/view_anomalies", methods=["GET"])
def view_anomalies():
    try:
        doc = db.collection("anomalies").document("log").get()
        if not doc.exists():
            return render_template("anomalies.html", anomalies=[])

        data = doc.to_dict()
        raw = data.get("events", [])
        if not isinstance(raw, list):
            print("[ERROR] events non è una lista:", type(raw))
            return render_template("anomalies.html", anomalies=[])

        anomalies = []
        for item in raw:
            if isinstance(item, dict):
                anomalies.append({
                    "timestamp": item.get("timestamp", "N/D"),
                    "actual": item.get("actual", "N/D"),
                    "predicted": item.get("predicted", "N/D"),
                    "delta": item.get("delta", "N/D"),
                    "sent": item.get("sent", False)
                })

        anomalies = sorted(anomalies, key=lambda x: x["timestamp"])
        return render_template("anomalies.html", anomalies=anomalies)

    except Exception as e:
        print("[ERROR] in view_anomalies:", e)
        return f"Errore durante la visualizzazione delle anomalie: {str(e)}", 500

# === Homepage con accesso alle varie funzionalità
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# === Per esecuzione locale (facoltativo)
if __name__ == "__main__":
    app.run(debug=True)

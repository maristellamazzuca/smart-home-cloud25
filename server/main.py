from flask import Flask, request, render_template
import os
from google.cloud import firestore
from server.anomaly_predictor import predict_and_alert

app = Flask(__name__)
db = firestore.Client()
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')

# === Parte 1: Cloud Run riceve dati dal client ===
@app.route("/receive_data", methods=["POST"])
def receive_data():
    return process_data(request, "Parte 1")

# === Parte 2: Simula una Cloud Function ma su Cloud Run ===
@app.route("/receive_data_cf", methods=["POST"])
def receive_data_cf():
    return process_data(request, "Parte 2")

# === Parte 3: Visualizzazione dati via HTTP (GET) ==== 
@app.route("/view_data", methods=["GET"])
def view_data():
    try:
        doc_ref = db.collection("sensors").document("sensor1")
        doc = doc_ref.get()

        if not doc.exists:
            return "Nessun dato trovato."

        data_dict = doc.to_dict()
        data_list = data_dict.get("data", [])

        # Ordina i dati per timestamp
        data_list = sorted(data_list, key=lambda x: x.get("timestamp", ""))

        # ✅ Estrai tutte le chiavi uniche da tutti i dizionari
        headers_set = set()
        for row in data_list:
            headers_set.update(row.keys())

        headers = sorted(headers_set)

        return render_template("view_data.html", data=data_list, headers=headers)

    except Exception as e:
        return f"Errore durante la lettura dei dati: {str(e)}", 500

# Funzione condivisa da parte1 e parte2
def process_data(request, parte):
    try:
        data = request.get_json()

        if not data or "timestamp" not in data or "use [kW]" not in data:
            return "Dati incompleti", 400

        timestamp = data.get("timestamp")
        doc_ref = db.collection("sensors").document("sensor1")

        # Salvataggio dati ricevuti
        if doc_ref.get().exists:
            doc_ref.update({"data": firestore.ArrayUnion([data])})
        else:
            doc_ref.set({"data": [data]})

        # === Parte 4: rilevamento e notifica anomalia ===
        current_value = float(data["use [kW]"])
        _, triggered = predict_and_alert(current_value, timestamp)

        return "Dati salvati" + (" con anomalia" if triggered else ""), 200

    except Exception as e:
        return f"Errore: {str(e)}", 500

@app.route("/view_anomalies", methods=["GET"])
def view_anomalies():
    try:
        doc = db.collection("anomalies").document("log").get()

        if not doc.exists:
            return render_template("anomalies.html", anomalies=[])

        raw = doc.to_dict().get("events", [])

        anomalies = sorted(raw, key=lambda x: x.get("timestamp", ""))

        return render_template("anomalies.html", anomalies=anomalies)

    except Exception as e:
        return f"Errore durante la lettura delle anomalie: {str(e)}", 500


# --- Index generale per test ---
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")
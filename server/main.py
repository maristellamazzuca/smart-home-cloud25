from flask import Flask, request, render_template
from google.cloud import firestore
import anomaly_predictor
import os

app = Flask(__name__)
db = firestore.Client()
app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')

# === Parte 1 e 2: ricezione dati da client (Cloud Run / Cloud Function simulata)
@app.route("/receive_data", methods=["POST"])
def receive_data():
    return process_data(request, "Parte 1")

@app.route("/receive_data_cf", methods=["POST"])
def receive_data_cf():
    return process_data(request, "Parte 2")

def process_data(request, parte):
    try:
        data = request.get_json()

        if not data or "timestamp" not in data or "use [kW]" not in data:
            return "Dati incompleti", 400

        timestamp = data.get("timestamp")
        doc_ref = db.collection("sensors").document("sensor1")

        # Salvataggio dei dati in Firestore
        if doc_ref.get().exists:
            doc_ref.update({"data": firestore.ArrayUnion([data])})
        else:
            doc_ref.set({"data": [data]})

        # === Parte 4: rilevamento anomalia e invio email se necessario
        try:
            current_value = float(data["use [kW]"])
            print(f"[DEBUG] use [kW]: {current_value}, timestamp: {timestamp}")
            result, triggered = anomaly_predictor.predict_and_alert(current_value, timestamp)
            print(f"[DEBUG] Risultato predizione: {result}, triggered: {triggered}")
        except Exception as e:
            print(f"[ERROR] Errore durante predict_and_alert: {e}")
            return f"Errore durante il rilevamento anomalia: {str(e)}", 500


        return "Dati salvati" + (" con anomalia" if triggered else ""), 200

    except Exception as e:
        return f"Errore: {str(e)}", 500

# === Parte 3: visualizzazione dei dati raccolti
@app.route("/view_data", methods=["GET"])
def view_data():
    try:
        doc = db.collection("sensors").document("sensor1").get()
        if not doc.exists:
            return render_template("view_data.html", data=[], headers=[])

        data_list = doc.to_dict().get("data", [])
        data_list = sorted(data_list, key=lambda x: x.get("timestamp", ""))

        headers = sorted(set().union(*(d.keys() for d in data_list if isinstance(d, dict))))
        return render_template("view_data.html", data=data_list, headers=headers)

    except Exception as e:
        return f"Errore durante la lettura dei dati: {str(e)}", 500

# === Parte 4 (visuale): visualizzazione anomalie rilevate
@app.route("/view_anomalies", methods=["GET"])
def view_anomalies():
    try:
        doc = db.collection("anomalies").document("log").get()
        if not doc.exists():
            print("Documento anomalies/log non esiste.")
            return render_template("anomalies.html", anomalies=[])

        data = doc.to_dict()
        print("Contenuto del documento anomalies/log:", data)

        raw = data.get("events", [])
        if not isinstance(raw, list):
            print("Campo 'events' non è una lista:", type(raw))
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
            else:
                print("Elemento malformato ignorato:", item)

        anomalies = sorted(anomalies, key=lambda x: x["timestamp"])
        return render_template("anomalies.html", anomalies=anomalies)

    except Exception as e:
        print("Errore in view_anomalies:", e)
        return f"Errore interno: {str(e)}", 500

# Pagina principale
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

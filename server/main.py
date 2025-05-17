from flask import Flask, request, render_template
from google.cloud import firestore
import numpy as np
import joblib
import smtplib
from email.mime.text import MIMEText
import os

# === Inizializzazione Flask e Firestore
app = Flask(__name__)
app.template_folder = "templates"
db = firestore.Client()

# === Parametri globali per la predizione (Parte 4a)
DELTA_THRESHOLD = 0.2
MODEL_PATH = "model.joblib"

# === Variabili ambiente per invio email (Parte 4b)
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# === Funzione per inviare una email in caso di anomalia (Parte 4b)
def send_email_alert(timestamp, actual, predicted):
    subject = "Smart Home - Anomalia rilevata"
    body = (
        f"Timestamp: {timestamp}\n"
        f"Valore misurato: {actual}\n"
        f"Valore previsto: {predicted:.2f}\n"
        f"Delta: {abs(actual - predicted):.2f}"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
        smtp.send_message(msg)

# === Parte 1-2: ricezione dati via POST (come da sensore IoT)
@app.route("/receive_data", methods=["POST"])
def receive_data():
    try:
        data = request.get_json()
        if not data or "timestamp" not in data or "use [kW]" not in data:
            return "Dati incompleti", 400

        timestamp = data["timestamp"]
        use_kw = float(data["use [kW]"])

        # Salvataggio su Firestore
        doc_ref = db.collection("sensors").document("sensor1")
        if doc_ref.get().exists():
            doc_ref.update({"data": firestore.ArrayUnion([data])})
        else:
            doc_ref.set({"data": [data]})

        # === Parte 4: predizione e rilevamento anomalia
        result, triggered = predict_and_notify(use_kw, timestamp)
        return "Dati salvati" + (" con anomalia" if triggered else ""), 200

    except Exception as e:
        print("[ERROR] in receive_data:", e)
        return f"Errore: {str(e)}", 500

# === Parte 4a: predizione + 4b: notifica se anomalia
def predict_and_notify(current_value, timestamp):
    try:
        model = joblib.load(MODEL_PATH)

        doc = db.collection("sensors").document("sensor1").get()
        history = [float(x["use [kW]"]) for x in doc.to_dict().get("data", []) if "use [kW]" in x]

        if len(history) < 4:
            return "Storico insufficiente", False

        x_input = np.array(history[-4:]).reshape(1, -1)
        predicted = model.predict(x_input)[0]
        delta = abs(current_value - predicted)

        if delta > DELTA_THRESHOLD:
            send_email_alert(timestamp, current_value, predicted)

            # Salva log in Firestore
            entry = {
                "timestamp": timestamp,
                "actual": current_value,
                "predicted": round(predicted, 2),
                "delta": round(delta, 2),
                "sent": True
            }
            log_ref = db.collection("anomalies").document("log")
            if log_ref.get().exists():
                log_ref.update({"events": firestore.ArrayUnion([entry])})
            else:
                log_ref.set({"events": [entry]})

            return "Anomalia rilevata", True

        return "Tutto regolare", False

    except Exception as e:
        print("[ERROR] in predict_and_notify:", e)
        return f"Errore: {str(e)}", False

# === Parte 3: visualizzazione dati raccolti
@app.route("/view_data")
def view_data():
    try:
        doc = db.collection("sensors").document("sensor1").get()
        if not doc.exists():
            return render_template("view_data.html", data=[], headers=[])
        data = doc.to_dict().get("data", [])
        headers = sorted(set().union(*(d.keys() for d in data if isinstance(d, dict))))
        return render_template("view_data.html", data=data, headers=headers)
    except Exception as e:
        return f"Errore: {str(e)}", 500

# === Parte 4b: visualizzazione anomalie salvate
@app.route("/view_anomalies")
def view_anomalies():
    try:
        doc = db.collection("anomalies").document("log").get()
        if not doc.exists():
            return render_template("anomalies.html", anomalies=[])

        raw = doc.to_dict().get("events", [])
        if not isinstance(raw, list):
            print("[WARNING] events non è una lista:", type(raw))
            return render_template("anomalies.html", anomalies=[])

        anomalies = []
        for item in raw:
            if isinstance(item, dict):
                anomalies.append(item)
            else:
                print("[WARNING] Trovato elemento non-dizionario in events:", type(item), item)

        anomalies = sorted(anomalies, key=lambda x: x.get("timestamp", ""))
        return render_template("anomalies.html", anomalies=anomalies)
    except Exception as e:
        print("[ERROR] in view_anomalies:", e)
        return f"Errore: {str(e)}", 500
# === Homepage
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

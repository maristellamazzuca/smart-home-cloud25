from flask import Flask, request, render_template
from google.cloud import firestore
import os
import smtplib
from email.mime.text import MIMEText
import numpy as np
import joblib

# === Configurazione Flask e Firestore
app = Flask(__name__)
app.template_folder = "templates"
db = firestore.Client()

# === Parametri modello e soglia anomalia (Parte 4a)
MODEL_PATH = "model.joblib"
DELTA_THRESHOLD = 0.2

# === Variabili ambiente per invio email (Parte 4b)
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# === Invio email in caso di anomalia
def send_email_alert(timestamp, actual, predicted):
    subject = "Smart Home - Anomalia rilevata"
    body = f"Timestamp: {timestamp}\\nValore misurato: {actual}\\nValore previsto: {predicted:.2f}\\nDelta: {abs(actual - predicted):.2f}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
        smtp.send_message(msg)

# === Parte 1-2: ricezione dati dal client
@app.route("/receive_data", methods=["POST"])
def receive_data():
    try:
        data = request.get_json()
        if not data or "timestamp" not in data or "use [kW]" not in data:
            return "Dati incompleti", 400

        timestamp = data["timestamp"]
        doc_ref = db.collection("sensors").document("sensor1")

        if doc_ref.get().exists():
            doc_ref.update({"data": firestore.ArrayUnion([data])})
        else:
            doc_ref.set({"data": [data]})

        # === Parte 4a: predizione
        result, triggered = predict_and_notify(data["use [kW]"], timestamp)
        return "Dati salvati" + (" con anomalia" if triggered else ""), 200

    except Exception as e:
        print("Errore in receive_data:", e)
        return f"Errore interno: {str(e)}", 500

# === Parte 4a/4b: predizione + notifica se necessario
def predict_and_notify(current_value, timestamp):
    try:
        model = joblib.load(MODEL_PATH)
        doc = db.collection("sensors").document("sensor1").get()
        history = [float(x["use [kW]"]) for x in doc.to_dict().get("data", []) if "use [kW]" in x]

        if len(history) < 4:
            return "Storico insufficiente", False

        x_input = np.array(history[-4:]).reshape(1, -1)
        predicted = model.predict(x_input)[0]
        delta = abs(float(current_value) - predicted)

        if delta > DELTA_THRESHOLD:
            send_email_alert(timestamp, float(current_value), predicted)
            log_ref = db.collection("anomalies").document("log")
            entry = {
                "timestamp": timestamp,
                "actual": float(current_value),
                "predicted": round(predicted, 2),
                "delta": round(delta, 2),
                "sent": True
            }
            if log_ref.get().exists():
                log_ref.update({"events": firestore.ArrayUnion([entry])})
            else:
                log_ref.set({"events": [entry]})
            return "Anomalia rilevata", True

        return "Normale", False
    except Exception as e:
        print("Errore in predict_and_notify:", e)
        return f"Errore: {str(e)}", False

# === Parte 3: visualizzazione dei dati
@app.route("/view_data")
def view_data():
    try:
        doc = db.collection("sensors").document("sensor1").get()
        data = doc.to_dict().get("data", []) if doc.exists else []
        headers = sorted(set().union(*(d.keys() for d in data)))
        return render_template("view_data.html", data=data, headers=headers)
    except Exception as e:
        return f"Errore: {str(e)}", 500

# === Parte 4b: visualizzazione anomalie
@app.route("/view_anomalies")
def view_anomalies():
    try:
        doc = db.collection("anomalies").document("log").get()
        events = doc.to_dict().get("events", []) if doc.exists else []
        return render_template("anomalies.html", anomalies=events)
    except Exception as e:
        return f"Errore: {str(e)}", 500

# === Homepage
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

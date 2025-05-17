import os
import numpy as np
import joblib
import smtplib
from email.mime.text import MIMEText
from google.cloud import firestore

# === Parametri
DELTA_THRESHOLD = 1.0
MODEL_PATH = "model.joblib"

# === Variabili ambiente per email
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

# === Inizializzazione
db = firestore.Client()

# === Funzione invio email via Gmail SMTP
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

# === Funzione per predizione e rilevamento anomalia
def predict_and_alert(current_value, timestamp):
    model = joblib.load(MODEL_PATH)

    doc = db.collection("sensors").document("sensor1").get()
    if not doc.exists():
        return "Nessun documento", False

    data = doc.to_dict().get("data", [])
    history = [float(x["use [kW]"]) for x in data if "use [kW]" in x]
    if len(history) < 4:
        return "Storico insufficiente", False

    x_input = np.array(history[-4:]).reshape(1, -1)
    predicted = model.predict(x_input)[0]

    if abs(current_value - predicted) > DELTA_THRESHOLD:
        send_email_alert(timestamp, current_value, predicted)

        # Log dell'anomalia per visualizzazione
        log_ref = db.collection("anomalies").document("log")
        anomaly = {
            "timestamp": timestamp,
            "actual": current_value,
            "predicted": round(predicted, 2),
            "delta": round(abs(current_value - predicted), 2),
            "sent": True
        }
        if log_ref.get().exists:
            log_ref.update({"events": firestore.ArrayUnion([anomaly])})
        else:
            log_ref.set({"events": [anomaly]})

        return "Anomalia rilevata", True

    return "Tutto regolare", False

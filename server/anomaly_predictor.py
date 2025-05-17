import os
import numpy as np
import joblib
import smtplib
from email.mime.text import MIMEText
from google.cloud import firestore

DELTA_THRESHOLD = 0.2
MODEL_PATH = "model.joblib"

EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")

db = firestore.Client()

def send_email_alert(timestamp, actual, predicted):
    subject = "Smart Home - Anomalia rilevata"
    body = f"Timestamp: {timestamp}\nValore misurato: {actual}\nValore previsto: {predicted:.2f}\nDelta: {abs(actual - predicted):.2f}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
        smtp.send_message(msg)

def predict_and_alert(current_value, timestamp):
    try:
        model = joblib.load(MODEL_PATH)
        doc = db.collection("sensors").document("sensor1").get()
        if not doc.exists():
            return "Nessun dato storico", False

        data = doc.to_dict().get("data", [])
        values = [float(x["use [kW]"]) for x in data if "use [kW]" in x]

        if len(values) < 4:
            return "Dati insufficienti", False

        x_input = np.array(values[-4:]).reshape(1, -1)
        predicted = model.predict(x_input)[0]
        delta = abs(current_value - predicted)

        if delta > DELTA_THRESHOLD:
            send_email_alert(timestamp, current_value, predicted)
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
        print("[ERROR] predict_and_alert:", e)
        return f"Errore: {e}", False

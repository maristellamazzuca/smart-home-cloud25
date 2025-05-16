import os
import numpy as np
import joblib
from google.cloud import firestore
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# Parametri
DELTA_THRESHOLD = 1.0
MODEL_PATH = "model.joblib"

# Inizializza Firestore e carica modello
db = firestore.Client()
model = joblib.load(MODEL_PATH)

# Email (SendGrid) - variabili ambiente
EMAIL_FROM = os.environ.get("EMAIL_FROM")
EMAIL_TO = os.environ.get("EMAIL_TO")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

def predict_and_alert(current_value, timestamp):
    # Recupera dati storici da Firestore
    doc = db.collection("sensors").document("sensor1").get()
    if not doc.exists:
        return "Nessun documento", False

    records = doc.to_dict().get("data", [])
    history = [float(r["use [kW]"]) for r in records if "use [kW]" in r]
    if len(history) < 4:
        return "Dati storici insufficienti", False

    # Predizione con gli ultimi 4 valori
    x_input = np.array(history[-4:]).reshape(1, -1)
    predicted = model.predict(x_input)[0]

    # Controlla anomalia
    if abs(current_value - predicted) > DELTA_THRESHOLD:
        subject = "Anomalia Smart Home rilevata"
        content = (
            f"Timestamp: {timestamp}\n"
            f"Valore misurato: {current_value}\n"
            f"Valore previsto: {predicted:.2f}\n"
            f"Delta: {abs(current_value - predicted):.2f}"
        )
        # Invio email
        message = Mail(from_email=EMAIL_FROM, to_emails=EMAIL_TO,
                       subject=subject, plain_text_content=content)
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        return "Anomalia rilevata e email inviata", True

    return "Nessuna anomalia", False

# Log dell’anomalia
log_ref = db.collection("anomalies").document("log")
entry = {
    "timestamp": timestamp,
    "actual": current_value,
    "predicted": round(predicted, 2),
    "delta": round(abs(current_value - predicted), 2),
    "sent": True
}
if log_ref.get().exists:
    log_ref.update({"events": firestore.ArrayUnion([entry])})
else:
    log_ref.set({"events": [entry]})

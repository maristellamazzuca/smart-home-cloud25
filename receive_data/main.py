import functions_framework
from google.cloud import firestore
from flask import Request

db = firestore.Client()

@functions_framework.http
def receive_data(request: Request):
    try:
        request_json = request.get_json(silent=True)
        timestamp = request_json.get("timestamp")
        value = float(request_json.get("value"))

        doc_ref = db.collection("sensors").document("sensor1")
        new_entry = {"timestamp": timestamp, "value": value}

        if doc_ref.get().exists:
            doc_ref.update({"data": firestore.ArrayUnion([new_entry])})
        else:
            doc_ref.set({"data": [new_entry]})

        return ("Dati ricevuti e salvati", 200)
    except Exception as e:
        return (f"Errore: {str(e)}", 400)

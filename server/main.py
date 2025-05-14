from flask import Flask, request
from google.cloud import firestore

app = Flask(__name__)
db = firestore.Client()

@app.route("/receive_data", methods=["POST"])
def receive_data():
    try:
        data = request.get_json()
        timestamp = data.get("timestamp")
        value = float(data.get("value"))

        # ✅ Usa la collezione personalizzata 'smarthomecloud'
        doc_ref = db.collection("smarthomecloud").document("sensor1")
        new_entry = {"timestamp": timestamp, "value": value}

        if doc_ref.get().exists:
            doc_ref.update({"data": firestore.ArrayUnion([new_entry])})
        else:
            doc_ref.set({"data": [new_entry]})

        return "Dati ricevuti e salvati", 200
    except Exception as e:
        return f"Errore: {str(e)}", 400

@app.route("/", methods=["GET"])
def index():
    return "Server attivo su Cloud Run!", 200

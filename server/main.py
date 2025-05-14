@app.route("/receive_data", methods=["POST"])
def receive_data():
    try:
        data = request.get_json()
        print("📥 Dati ricevuti:", data)

        if not data:
            print("❌ JSON vuoto o malformato")
            return "Bad request: JSON vuoto o malformato", 400

        timestamp = data.get("timestamp")
        value_str = data.get("value")

        if not timestamp or not value_str:
            print("❗ Dati mancanti:", timestamp, value_str)
            return "Dati incompleti", 400

        try:
            value = float(value_str)
        except ValueError:
            print("❗ Valore non numerico:", value_str)
            return "Valore non numerico", 400

        doc_ref = db.collection("smarthomecloud").document("sensor1")
        new_entry = {"timestamp": timestamp, "value": value}

        if doc_ref.get().exists:
            doc_ref.update({"data": firestore.ArrayUnion([new_entry])})
        else:
            doc_ref.set({"data": [new_entry]})

        print("✅ Dato salvato:", new_entry)
        return "Dati ricevuti e salvati", 200

    except Exception as e:
        print("🔥 Errore server:", e)
        return f"Errore: {str(e)}", 400

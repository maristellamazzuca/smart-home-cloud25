from flask import Flask, request, render_template
import os
from google.cloud import firestore

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
        print(f"📥 [{parte}] Dati ricevuti:", data)

        if not data:
            return "Bad request: JSON vuoto o malformato", 400

        # timestamp resta per ordinamento/visualizzazione
        timestamp = data.get("timestamp")
        if not timestamp:
            return "Dati incompleti: manca timestamp", 400

        # Salva tutti i dati della riga
        doc_ref = db.collection("sensors").document("sensor1")
        if doc_ref.get().exists:
            doc_ref.update({"data": firestore.ArrayUnion([data])})
        else:
            doc_ref.set({"data": [data]})

        print(f"✅ [{parte}] Riga completa salvata.")
        return "Dati ricevuti e salvati", 200

    except Exception as e:
        print(f"🔥 [{parte}] Errore server:", e)
        return f"Errore: {str(e)}", 400


# --- Index generale per test ---
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")
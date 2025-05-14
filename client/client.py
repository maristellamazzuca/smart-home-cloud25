import csv
import time
import requests
from datetime import datetime, timezone

SERVER_URL = 'https://smart-home-multi-174184628218.europe-west1.run.app/receive_data'  # aggiorna con il tuo

def send_data(row):
    # Converte il timestamp Unix
    unix_time = int(row['time'])
    timestamp = datetime.fromtimestamp(unix_time, tz=timezone.utc).isoformat()

    # Crea un dizionario con tutti i campi, incluso il timestamp convertito
    payload = dict(row)
    payload['timestamp'] = timestamp

    headers = {
        'Content-Type': 'application/json'
    }

    print("Payload da inviare:", payload)
    try:
        response = requests.post(SERVER_URL, json=payload, headers=headers)
        print(f"Status: {response.status_code}")
    except Exception as e:
        print(f"Errore invio dati: {e}")

def main():
    with open('client/HomeC.csv', newline='') as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        reader.fieldnames = [name.strip() for name in reader.fieldnames]

        for row in reader:
            row = {key.strip(): value for key, value in row.items()}
            send_data(row)
            time.sleep(3)

if __name__ == '__main__':
    main()

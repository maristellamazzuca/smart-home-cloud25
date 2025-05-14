import csv
import time
import requests
from datetime import datetime

SERVER_URL = 'https://smart-home-server-174184628218.europe-west1.run.app/receive_data'  # Sostituisci con il tuo vero URL

def send_data(row):
    unix_time = int(row['time'])  # converti stringa in intero
    timestamp = datetime.utcfromtimestamp(unix_time).isoformat()  # es. '2016-01-01T00:00:00'

    payload = {
        'timestamp': timestamp,
        'value': row['use [kW]']
    }
    print("Payload da inviare:", payload)
    try:
        response = requests.post(SERVER_URL, json=payload)
        print(f"Sent: {payload} → Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    with open('client/HomeC.csv', newline='') as file:
        reader = csv.DictReader(file, skipinitialspace=True)
        reader.fieldnames = [name.strip() for name in reader.fieldnames]  # rimuove spazi in eccesso

        for row in reader:
            row = {key.strip(): value for key, value in row.items()}  # normalizza ogni chiave
            send_data(row)
            time.sleep(3)

if __name__ == '__main__':
    main()

import csv
import time
import requests
from datetime import datetime, timezone

SERVER_URL = 'https://smart-home-server-174184628218.europe-west1.run.app/receive_data'  # Sostituisci con il tuo vero URL

def send_data(row):
    from datetime import datetime, timezone
    unix_time = int(row['time'])
    timestamp = datetime.fromtimestamp(unix_time, tz=timezone.utc).isoformat()

    payload = {
        'timestamp': timestamp,
        'value': row['use [kW]']
    }

    headers = {
        'Content-Type': 'application/json'
    }

    print("Payload da inviare:", payload)
    try:
        response = requests.post(SERVER_URL, json=payload, headers=headers)
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
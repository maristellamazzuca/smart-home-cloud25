import csv
import time
import requests
from datetime import datetime, timezone

SERVER_URL = 'https://smart-home-server-174184628218.europe-west1.run.app/receive_data'  # metti il tuo URL qui

def send_data(row):
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
        print(f"Sent: {payload} → Status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

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

import csv
import time
import requests

SERVER_URL = 'https://smart-home-server-xxxxx-ew.a.run.app/receive_data'  # Sostituisci con il tuo vero URL

def send_data(row):
    payload = {
        'timestamp': row['time'],             # 'time' = timestamp in secondi UNIX
        'value': row['use [kW]']              # usa la colonna 'use [kW]' come valore
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

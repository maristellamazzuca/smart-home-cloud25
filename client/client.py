import csv
import time
import requests

# Inserirai qui l’URL della Cloud Function dopo il deploy
SERVER_URL = 'https://URL-DELLA-TUA-FUNZIONE.cloudfunctions.net/receive_data'

def send_data(row):
    payload = {
        'timestamp': row['timestamp'],
        'value': row['value']
    }
    try:
        response = requests.post(SERVER_URL, json=payload)
        print(f"Sent: {payload} → Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    with open('client/data.csv', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            send_data(row)
            time.sleep(3)  # invia un dato ogni 3 secondi

if __name__ == '__main__':
    main()

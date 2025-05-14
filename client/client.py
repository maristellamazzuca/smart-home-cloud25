import csv
import time
import requests

SERVER_URL = 'https://smart-home-server-abcde.a.run.app/receive_data'  # aggiorna con il tuo

def send_data(row):
    payload = {
        'timestamp': row['time'],             # usa 'time' invece di 'timestamp'
        'value': row['use [kW]']              # o qualsiasi altra colonna ti interessa
    }
    try:
        response = requests.post(SERVER_URL, json=payload)
        print(f"Sent: {payload} → Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    with open('client/HomeC.csv', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            send_data(row)
            time.sleep(3)

if __name__ == '__main__':
    main()

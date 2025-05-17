import csv
import time
import requests
from datetime import datetime, timezone

SERVER_URL = 'https://smart-home-multi-174184628218.europe-west1.run.app/receive_data'

FIELDNAMES = [
    'time', 'use [kW]', 'gen [kW]', 'House overall [kW]', 'Dishwasher [kW]',
    'Furnace 1 [kW]', 'Furnace 2 [kW]', 'Home office [kW]', 'Fridge [kW]',
    'Wine cellar [kW]', 'Garage door [kW]', 'Kitchen 12 [kW]', 'Kitchen 14 [kW]',
    'Kitchen 38 [kW]', 'Barn [kW]', 'Well [kW]', 'Microwave [kW]',
    'Living room [kW]', 'Solar [kW]', 'temperature', 'icon', 'humidity',
    'visibility', 'summary', 'apparentTemperature', 'pressure', 'windSpeed',
    'cloudCover', 'windBearing', 'precipIntensity', 'dewPoint', 'precipProbability'
]

def send_data(row):
    unix_time = int(row['time'])
    iso_timestamp = datetime.fromtimestamp(unix_time, tz=timezone.utc).isoformat()

    payload = {key: row.get(key, '') for key in FIELDNAMES}
    payload['timestamp_unix'] = row.get('time', '')
    payload['timestamp'] = iso_timestamp

    headers = {'Content-Type': 'application/json'}
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

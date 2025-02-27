import requests
import json
import os

otx_pulse_ids = "https://otx.alienvault.com/api/v1/pulses/subscribed_pulse_ids"
#otx_api_pulse_url = "https://otx.alienvault.com/api/v1/pulses/60ece5998a5b54a5ffe75cb4/indicators"
otx_api_key = "c161c08ef77dceeb929c940d06fa61efde7ac1f9ab99a59ff8165fe59d029840"

def fetch_pulses(api_url, api_key):
    headers = {'X-OTX-API-KEY': api_key}
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data from {api_url}")
        return None

def fetch_threat_intel(api_url, api_key):
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data from {api_url}")
        return None

pulse_data = fetch_pulses(otx_pulse_ids, otx_api_key)
if pulse_data:
    print(json.dumps(pulse_data, indent=2))
    print(pulse_data["results"])

    for result in pulse_data["results"]:
        otx_api_pulse_url = f"https://otx.alienvault.com/api/v1/pulses/{result}/indicators"
        otx_data = fetch_threat_intel(otx_api_pulse_url, otx_api_key)
        if otx_data:
            directory = "otx_data"
            if not os.path.exists(directory):
                os.makedirs(directory)
            with open(os.path.join(directory, f"{result}.json"), "w") as f:
                json.dump(otx_data, f, indent=2)
else:
    print("No pulse data fetched.")
    




# Example usage


# python schedulellavoi laittaa vaikka ajaan kerran tunnissa
# Hakee tietoja cassandra databaseen kuten ioc, threat actors, malware, vulns, incidents
import os
import requests
import json

# Determine the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, 'output.json')

# Fetch data from the API
res = requests.get('https://www.ransomlook.io/api/last')

# Check if the request was successful
if res.status_code == 200:
    data = res.json()
    # Write the data to output.json in the script's directory
    with open(output_path, 'w') as file:
        json.dump(data, file, indent=4)
else:
    print(f"Failed to fetch data. Status code: {res.status_code}")

print(data)

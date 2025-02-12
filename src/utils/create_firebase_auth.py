import os
import json

# Path to the service account file
file_path = 'serviceAccount.json'

# Check if the file already exists
if not os.path.exists(file_path):
    # Get the service account JSON from the environment variable
    service_account_json = os.getenv('FIREBASE')
    
    # Write the JSON to a file if the environment variable is set
    if service_account_json:
        with open(file_path, 'w') as f:
            f.write(service_account_json)
        print(f"Service account JSON written to {file_path}.")
    else:
        print("FIREBASE environment variable is not set.")
else:
    print(f"{file_path} already exists.")

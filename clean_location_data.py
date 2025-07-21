import json
import re

def clean_location_data(file_path):
    """
    Cleans the klook_location field in the provided JSON file based on specific rules.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading file {file_path}: {e}")
        return

    # Regex to find latitude,longitude patterns
    # Handles variations in spacing and potential floating point numbers
    coord_pattern = re.compile(r'(\s*,\s*)?(\-?\d{1,3}\.\d+,\-?\d{1,3}\.\d+)\s*')

    for item in data:
        if not isinstance(item, dict):
            continue

        location = item.get('klook_location')

        if not isinstance(location, dict):
            continue

        address = location.get('address')
        coordinates = location.get('coordinates')

        # Rule 3: If address is missing or empty, set to "Hong Kong"
        if not address:
            location['address'] = "Hong Kong"
            continue

        # Rule 2: If address is just coordinates, set to "Hong Kong"
        # We check if the address, after removing spaces, matches the coordinates string
        if isinstance(coordinates, str) and address.strip() == coordinates.strip():
            location['address'] = "Hong Kong"
            continue

        # Rule 1: If address contains coordinates, remove them
        if isinstance(address, str):
            # Use regex to find and remove coordinate-like patterns from the address
            cleaned_address = coord_pattern.sub('', address).strip(' ,')
            
            # If cleaning results in an empty string, set to "Hong Kong"
            if not cleaned_address:
                 location['address'] = "Hong Kong"
            else:
                 location['address'] = cleaned_address


    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Successfully cleaned and updated {file_path}")
    except IOError as e:
        print(f"Error writing to file {file_path}: {e}")

if __name__ == '__main__':
    clean_location_data('klook_activity_data.json')
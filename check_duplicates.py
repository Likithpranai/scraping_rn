import json
from collections import Counter

def remove_duplicate_ids(file_path):
    """
    Reads a JSON file, removes objects with duplicate 'id' values, keeping the first occurrence,
    and writes the cleaned data back to the file.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' is not a valid JSON file.")
        return

    if not isinstance(data, list):
        print("Error: The JSON data is not a list of objects.")
        return

    seen_ids = set()
    unique_items = []
    duplicate_ids_found = []

    for item in data:
        item_id = item.get('id')
        if item_id is not None:
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_items.append(item)
            else:
                duplicate_ids_found.append(item_id)
        else:
            # Keep items without an id
            unique_items.append(item)

    if duplicate_ids_found:
        print("Removed duplicate items for the following IDs:")
        for dup_id in sorted(list(set(duplicate_ids_found))):
            print(f"  ID: {dup_id}")
        
        try:
            with open(file_path, 'w') as f:
                json.dump(unique_items, f, indent=4)
            print(f"\nSuccessfully removed duplicates and updated '{file_path}'.")
            print(f"Original item count: {len(data)}")
            print(f"New item count: {len(unique_items)}")

        except IOError:
            print(f"Error: Could not write to file '{file_path}'.")

    else:
        print("No duplicate IDs found.")

if __name__ == "__main__":
    remove_duplicate_ids('structured_activity_data.json')

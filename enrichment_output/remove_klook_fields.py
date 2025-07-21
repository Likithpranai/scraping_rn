import json

def remove_klook_fields(input_file, output_file):
    """
    Reads a JSON file, removes all keys that start with 'klook_',
    and saves the cleaned data to a new JSON file.

    Args:
        input_file (str): The path to the input JSON file.
        output_file (str): The path to the output JSON file.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            print("Warning: JSON data is not a list of objects.")
            # Handle non-list JSON if necessary, e.g., if it's a single object
            if isinstance(data, dict):
                cleaned_data = {k: v for k, v in data.items() if not k.startswith('klook_')}
            else:
                cleaned_data = data # Or handle other types as needed
        else:
            cleaned_data = []
            for item in data:
                if isinstance(item, dict):
                    cleaned_item = {k: v for k, v in item.items() if not k.startswith('klook_')}
                    cleaned_data.append(cleaned_item)
                else:
                    cleaned_data.append(item) # Keep non-dict items as is

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=4, ensure_ascii=False)

        print(f"Successfully processed {input_file} and saved cleaned data to {output_file}")

    except FileNotFoundError:
        print(f"Error: The file {input_file} was not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file {input_file}.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    # Define the input and output file paths
    # You can change these to whatever files you need to process
    input_json_file = 'enrichment_output/enriched_klook_data.json'
    output_json_file = 'klook_data.json'
    
    remove_klook_fields(input_json_file, output_json_file)

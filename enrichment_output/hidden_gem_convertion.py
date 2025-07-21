import json

# File path
file_path = '/Users/kitlonglui/Desktop/roameo_all/roameo-generic-scraper/enrichment_output/enriched_klook_data.json'
output_file_path = '/Users/kitlonglui/Desktop/roameo_all/roameo-generic-scraper/enrichment_output/updated_enriched_klook_data.json'

# Read the JSON data from the file
try:
    with open(file_path, 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"Error: The file {file_path} was not found.")
    exit()
except json.JSONDecodeError:
    print(f"Error: The file {file_path} is not a valid JSON file.")
    exit()

# Iterate through the list of objects and update the 'enrich_hiddenGemScore'
for item in data:
    if 'enrich_hiddenGemScore' in item and isinstance(item['enrich_hiddenGemScore'], (int, float)):
        item['enrich_hiddenGemScore'] *= 10

# Write the updated data back to a new file to avoid data loss, and for inspection
with open(output_file_path, 'w') as f:
    json.dump(data, f, indent=4)

print(f"Successfully multiplied 'enrich_hiddenGemScore' by 10 and saved to {output_file_path}")

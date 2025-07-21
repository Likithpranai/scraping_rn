import json

# Load the translated_cityline_data.json file
with open('cityline/translated_cityline_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Remove the 'cityline_name' field from all objects
for obj in data:
    obj.pop('cityline_name', None)

# Save the result to cityline_data.json
with open('cityline_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

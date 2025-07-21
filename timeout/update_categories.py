#!/usr/bin/env python3
import json

# Load the JSON file
with open('timeout_bars.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Track changes
changes_made = 0

# Update all "Bar" entries to "Bars and pubs"
for entry in data:
    if 'source_categories' in entry and len(entry['source_categories']) > 0:
        for i, category in enumerate(entry['source_categories']):
            if category == "Bar":
                entry['source_categories'][i] = "Bars and pubs"
                changes_made += 1

# Save the updated JSON file
with open('timeout_bars.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Updated {changes_made} 'Bar' entries to 'Bars and pubs'")

#!/usr/bin/env python3
import json

# Load the JSON file
with open('timeout_bars.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Track changes
entries_updated = 0

# Add enrich_localName and enrich_englishName fields to all entries
for entry in data:
    if 'source_name' in entry:
        entry['enrich_localName'] = entry['source_name']
        entry['enrich_englishName'] = entry['source_name']
        entries_updated += 1

# Save the updated JSON file
with open('timeout_bars.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Added enrich_localName and enrich_englishName to {entries_updated} entries")

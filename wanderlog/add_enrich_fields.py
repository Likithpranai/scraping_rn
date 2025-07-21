#!/usr/bin/env python3
import json

def main():
    try:
        # Read the existing JSON file
        with open('hong_kong_bars_precise.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep track of how many entries were updated
        updated_count = 0
        
        # Update each bar entry with enrich_localName and enrich_englishName
        for bar in data.get('bars', []):
            # Get source_name
            source_name = bar.get('source_name', '')
            
            # Add enrich_localName and enrich_englishName fields
            bar['enrich_localName'] = source_name
            bar['enrich_englishName'] = source_name
            
            updated_count += 1
            print(f"Updated {source_name}")
        
        # Write the updated data back to the file
        with open('hong_kong_bars_precise.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nAdded enrich_localName and enrich_englishName to {updated_count} entries")
    
    except Exception as e:
        print(f"Error updating JSON file: {e}")

if __name__ == "__main__":
    main()

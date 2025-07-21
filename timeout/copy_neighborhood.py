#!/usr/bin/env python3
import json

def main():
    try:
        # Read the existing JSON file
        with open('timeout_bars.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep track of how many entries were updated
        updated_count = 0
        
        # Copy enrich_neighborhood to source_neighbourhood for each entry
        for entry in data:
            if 'enrich_neighborhood' in entry:
                entry['source_neighbourhood'] = entry['enrich_neighborhood']
                updated_count += 1
                print(f"Updated source_neighbourhood for {entry.get('source_name', 'unknown')}: {entry['enrich_neighborhood']}")
        
        # Write the updated data back to the file
        with open('timeout_bars.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"\nCopied enrich_neighborhood to source_neighbourhood for {updated_count} entries")
    
    except Exception as e:
        print(f"Error updating JSON file: {e}")

if __name__ == "__main__":
    main()

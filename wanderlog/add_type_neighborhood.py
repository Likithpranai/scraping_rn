#!/usr/bin/env python3
import json

def add_type_and_neighborhood():
    """
    Add enrich_type (from first element of source_category) and 
    enrich_neighborhood (from source_neighbourhood) to all entries in the JSON file.
    """
    try:
        # Read the existing JSON file
        with open('hong_kong_bars_precise.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep track of how many entries were updated
        updated_count = 0
        
        # Update each bar entry
        for bar in data.get('bars', []):
            bar_name = bar.get('source_name', 'unknown')
            
            # Add enrich_type from first element of source_category
            if 'source_category' in bar and bar['source_category']:
                if isinstance(bar['source_category'], list) and len(bar['source_category']) > 0:
                    bar['enrich_type'] = bar['source_category'][0]
                    print(f"Added enrich_type '{bar['enrich_type']}' to {bar_name}")
                else:
                    bar['enrich_type'] = "Bar"
                    print(f"Added default enrich_type 'Bar' to {bar_name} (no source_category list)")
            else:
                bar['enrich_type'] = "Bar"
                print(f"Added default enrich_type 'Bar' to {bar_name} (no source_category)")
            
            # Add enrich_neighborhood from source_neighbourhood
            if 'source_neighbourhood' in bar and bar['source_neighbourhood']:
                bar['enrich_neighborhood'] = bar['source_neighbourhood']
                print(f"Added enrich_neighborhood '{bar['enrich_neighborhood']}' to {bar_name}")
            else:
                bar['enrich_neighborhood'] = "Hong Kong"
                print(f"Added default enrich_neighborhood 'Hong Kong' to {bar_name} (no source_neighbourhood)")
            
            updated_count += 1
        
        # Write the updated data back to the file
        with open('hong_kong_bars_precise.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSummary: Added enrich_type and enrich_neighborhood to {updated_count} entries")
        print(f"Total bars processed: {len(data.get('bars', []))}")
    
    except Exception as e:
        print(f"Error updating JSON file: {e}")

def main():
    print("Adding enrich_type and enrich_neighborhood to all entries...")
    add_type_and_neighborhood()

if __name__ == "__main__":
    main()

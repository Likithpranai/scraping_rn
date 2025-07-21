#!/usr/bin/env python3
import json

def main():
    try:
        # Read the existing JSON file
        with open('timeout_bars.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep track of how many entries were updated
        updated_count = 0
        
        # Update each entry with enrich_type and enrich_neighborhood
        for entry in data:
            # Get source_categories (should be a list with one item "Bars and pubs")
            source_categories = entry.get('source_categories', [])
            if source_categories:
                # Use the first category as enrich_type
                entry['enrich_type'] = source_categories[0]
            else:
                # Default value if source_categories is empty
                entry['enrich_type'] = "Bars and pubs"
            
            # Extract neighborhood from address (last two parts of the comma-separated address)
            address = entry.get('source_address', '')
            if address and ',' in address:
                address_parts = [part.strip() for part in address.split(',')]
                if len(address_parts) >= 2:
                    # Get the last two parts of the address
                    neighborhood = f"{address_parts[-2]}, {address_parts[-1]}"
                    entry['enrich_neighborhood'] = neighborhood
                    print(f"Extracted neighborhood: {neighborhood}")
                else:
                    # If address doesn't have enough parts, use the whole address
                    entry['enrich_neighborhood'] = address
                    print(f"Using full address as neighborhood: {address}")
            else:
                # Fallback to source_neighbourhood if address parsing fails
                source_neighborhood = entry.get('source_neighbourhood', '')
                entry['enrich_neighborhood'] = source_neighborhood
                print(f"Using source_neighbourhood: {source_neighborhood}")
            
            updated_count += 1
        
        # Write the updated data back to the file
        with open('timeout_bars.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"Added enrich_type and enrich_neighborhood to {updated_count} entries")
    
    except Exception as e:
        print(f"Error updating JSON file: {e}")

if __name__ == "__main__":
    main()

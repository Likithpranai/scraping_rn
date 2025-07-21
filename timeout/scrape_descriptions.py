#!/usr/bin/env python3
import json
import requests
import re
from bs4 import BeautifulSoup

# Set up headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def extract_descriptions_from_page(url):
    """Extract descriptions for bars from the main list page"""
    print(f"Fetching content from {url}...")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Dictionary to store bar name -> description mapping
        bar_descriptions = {}
        
        # Find all article sections
        articles = soup.find_all('article')
        
        for article in articles:
            # Try to find the bar name
            name_elem = article.find(['h3', 'h2', 'h1'])
            
            if not name_elem:
                continue
                
            # Clean up the bar name (remove any numbering)
            bar_name = re.sub(r'^\\d+\\.\\s*', '', name_elem.get_text().strip())
            
            # Find the summary section
            summary_div = article.find('div', {'data-testid': 'summary_testID'})
            if summary_div:
                # Find the first paragraph that contains "What is it?"
                paragraphs = summary_div.find_all('p')
                for p in paragraphs:
                    if 'What is it?' in p.text:
                        # Extract the text after "What is it?"
                        description = p.text.replace('What is it?', '', 1).strip()
                        if description:
                            bar_descriptions[bar_name] = description
                            print(f"Found description for {bar_name}: {description[:50]}...")
                            break
        
        return bar_descriptions
    
    except Exception as e:
        print(f"Error extracting descriptions from {url}: {e}")
        return {}

def update_json_with_descriptions(bar_descriptions):
    """Update the JSON file with the scraped descriptions"""
    try:
        # Read the existing JSON file
        with open('timeout_bars.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep track of how many entries were updated
        updated_count = 0
        default_count = 0
        
        # Update each entry with its corresponding description
        for entry in data:
            bar_name = entry.get('source_name', '')
            
            # Try to find an exact match
            if bar_name in bar_descriptions:
                entry['enrich_description'] = bar_descriptions[bar_name]
                print(f"Added description to {bar_name}")
                updated_count += 1
            else:
                # Try to find a partial match
                found_match = False
                for desc_name, desc in bar_descriptions.items():
                    if bar_name.lower() in desc_name.lower() or desc_name.lower() in bar_name.lower():
                        entry['enrich_description'] = desc
                        print(f"Added description to {bar_name} (partial match with {desc_name})")
                        updated_count += 1
                        found_match = True
                        break
                
                if not found_match:
                    # Create a default description for bars without descriptions
                    default_desc = f"{bar_name} is one of Hong Kong's recommended bars featured in Time Out's best bars list."
                    entry['enrich_description'] = default_desc
                    print(f"Added default description to {bar_name}")
                    default_count += 1
        
        # Write the updated data back to the file
        with open('timeout_bars.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"\nSummary: Added actual descriptions to {updated_count} entries and default descriptions to {default_count} entries (total: {len(data)} entries)")
    
    except Exception as e:
        print(f"Error updating JSON file: {e}")

def main():
    # URL of the main list page
    main_url = "https://www.timeout.com/hong-kong/bars-and-pubs/best-bars-hong-kong"
    
    # Scrape all bar descriptions from the main page
    bar_descriptions = extract_descriptions_from_page(main_url)
    
    # Update the JSON file with the scraped descriptions
    update_json_with_descriptions(bar_descriptions)

if __name__ == "__main__":
    main()

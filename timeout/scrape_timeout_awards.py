#!/usr/bin/env python3
import json
import requests
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Set up headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def extract_awards_from_page(url):
    """Extract Time Out Awards from a bar's detail page"""
    try:
        print(f"Fetching content from {url}...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the Time Out Awards section
        awards_header = soup.find('h3', string=lambda s: s and 'Time Out Awards' in s)
        
        if not awards_header:
            # Try alternative approach - find by class and style
            awards_header = soup.find('h3', class_=lambda c: c and 'xs-text-3' in c, 
                                     style=lambda s: s and 'border-top: 4px solid #000000' in s)
        
        awards = []
        if awards_header:
            # Find the awards content - typically in paragraphs or list items after the header
            award_elements = []
            
            # Look for elements after the awards header
            next_elem = awards_header.find_next_sibling()
            while next_elem and not (next_elem.name == 'h3' or next_elem.name == 'h2'):
                if next_elem.name == 'p' or next_elem.name == 'li':
                    award_text = next_elem.get_text().strip()
                    if award_text:
                        award_elements.append(award_text)
                next_elem = next_elem.find_next_sibling()
            
            # If no awards found in siblings, try looking for specific elements inside a container
            if not award_elements:
                award_container = awards_header.find_parent('div')
                if award_container:
                    award_elements = [elem.get_text().strip() for elem in award_container.find_all(['p', 'li']) 
                                     if elem.get_text().strip() and elem != awards_header]
            
            # Clean up award texts
            for award in award_elements:
                # Remove any extra whitespace and clean up
                clean_award = re.sub(r'\s+', ' ', award).strip()
                if clean_award:
                    awards.append(clean_award)
        
        return awards
    
    except Exception as e:
        print(f"Error extracting awards from {url}: {e}")
        return []

def main():
    try:
        # Load the JSON file
        with open('timeout_bars.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        base_url = "https://www.timeout.com"
        awards_count = 0
        bars_with_awards = 0
        
        # Process each bar
        for entry in data:
            bar_name = entry.get('source_name', '')
            
            # Extract the detail page URL from the main URL
            main_url = entry.get('source_url', '')
            
            # Check if we have a detail URL in the JSON
            detail_path = None
            
            # Try to construct a detail URL based on the bar name
            if bar_name:
                # Convert bar name to URL-friendly format
                slug = bar_name.lower().replace(' ', '-').replace(':', '').replace('\'', '')
                detail_path = f"/hong-kong/bars-and-pubs/{slug}"
            
            if detail_path:
                detail_url = urljoin(base_url, detail_path)
                
                # Extract awards from the detail page
                awards = extract_awards_from_page(detail_url)
                
                if awards:
                    entry['enrich_recognition'] = awards
                    print(f"Added {len(awards)} awards to {bar_name}")
                    awards_count += len(awards)
                    bars_with_awards += 1
                else:
                    # Set empty array as default
                    entry['enrich_recognition'] = []
                    print(f"No awards found for {bar_name}")
                
                # Be nice to the server
                time.sleep(1)
            else:
                # Set empty array as default
                entry['enrich_recognition'] = []
                print(f"Could not determine detail URL for {bar_name}")
        
        # Save the updated JSON file
        with open('timeout_bars.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"\nSummary: Added {awards_count} awards to {bars_with_awards} bars (out of {len(data)} total)")
    
    except Exception as e:
        print(f"Error in main function: {e}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import json
import requests
import re
from bs4 import BeautifulSoup
import time

# Headers to mimic a browser visit
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Connection': 'keep-alive',
    'Referer': 'https://www.timeout.com/'
}

def scrape_all_bar_tips(url):
    """Scrape all bar tips from the main list page"""
    print(f"Fetching content from {url}...")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Dictionary to store bar name -> tip mapping
        bar_tips = {}
        
        # Find all article sections
        articles = soup.find_all('article')
        
        for article in articles:
            # Try to find the bar name
            name_elem = article.find(['h3', 'h2', 'h1'])
            
            if not name_elem:
                continue
                
            # Clean up the bar name (remove any numbering)
            bar_name = re.sub(r'^\d+\.\s*', '', name_elem.get_text().strip())
            
            # Find paragraphs that contain "Time Out tip:"
            paragraphs = article.find_all('p')
            for p in paragraphs:
                if 'Time Out tip:' in p.text:
                    # Find the span with font-weight: 400 after the "Time Out tip:" text
                    spans = p.find_all('span', style=lambda s: s and 'font-weight: 400' in s)
                    if spans:
                        tip_text = ''.join(span.get_text() for span in spans).strip()
                        if tip_text:
                            bar_tips[bar_name] = tip_text
                            print(f"Found tip for {bar_name}: {tip_text[:50]}...")
                            break
                    else:
                        # If no span found, try to extract text after "Time Out tip:"
                        tip_text = p.text.split('Time Out tip:', 1)[1].strip()
                        if tip_text:
                            bar_tips[bar_name] = tip_text
                            print(f"Found tip for {bar_name}: {tip_text[:50]}...")
                            break
        
        return bar_tips
    
    except Exception as e:
        print(f"Error scraping tips from {url}: {e}")
        return {}

def update_json_with_tips(bar_tips):
    """Update the JSON file with the scraped tips"""
    try:
        # Read the existing JSON file
        with open('timeout_bars.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep track of how many entries were updated
        updated_count = 0
        default_count = 0
        
        # Update each entry with its corresponding tip
        for entry in data:
            bar_name = entry.get('source_name', '')
            
            # Try to find an exact match
            if bar_name in bar_tips:
                entry['enrich_localTips'] = bar_tips[bar_name]
                print(f"Added tip to {bar_name}")
                updated_count += 1
            else:
                # Try to find a partial match
                found_match = False
                for tip_name, tip in bar_tips.items():
                    if bar_name.lower() in tip_name.lower() or tip_name.lower() in bar_name.lower():
                        entry['enrich_localTips'] = tip
                        print(f"Added tip to {bar_name} (partial match with {tip_name})")
                        updated_count += 1
                        found_match = True
                        break
                
                if not found_match:
                    # Create a default tip for bars without tips
                    default_tip = f"Visit {bar_name} for a unique bar experience in Hong Kong. Be sure to check their signature cocktails and atmosphere that make this spot a Time Out recommendation."
                    entry['enrich_localTips'] = default_tip
                    print(f"Added default tip to {bar_name}")
                    default_count += 1
        
        # Write the updated data back to the file
        with open('timeout_bars.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"\nSummary: Added actual tips to {updated_count} entries and default tips to {default_count} entries (total: {len(data)} entries)")
    
    except Exception as e:
        print(f"Error updating JSON file: {e}")

def main():
    # Load the JSON file
    with open('timeout_bars.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Get the main URL from the first entry
    main_url = "https://www.timeout.com/hong-kong/bars-and-pubs/best-bars-hong-kong"
    
    # Scrape all bar tips from the main page
    bar_tips = scrape_all_bar_tips(main_url)
    
    # Update the JSON file with the scraped tips
    update_json_with_tips(bar_tips)

if __name__ == "__main__":
    main()

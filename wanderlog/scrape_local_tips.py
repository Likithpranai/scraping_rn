#!/usr/bin/env python3
import json
import requests
import time
import re
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Set up headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def extract_tips_from_detail_page(url, max_retries=3):
    """Extract 'Know before you go' tips from a bar's detail page"""
    print(f"Fetching content from {url}...")
    
    for attempt in range(max_retries):
        try:
            # Add a much longer delay with randomization to be respectful to the server and avoid rate limiting
            delay = 10 + random.uniform(2, 5)  # Random delay between 10-15 seconds
            print(f"Waiting {delay:.1f} seconds before request (attempt {attempt+1}/{max_retries})...")
            time.sleep(delay)
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # If we get here, the request was successful
            break
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:  # Last attempt
                print(f"All {max_retries} attempts failed for {url}")
                raise
            # Wait longer before retrying
            retry_delay = 20 + random.uniform(5, 10)  # 20-30 seconds
            print(f"Waiting {retry_delay:.1f} seconds before retrying...")
            time.sleep(retry_delay)
    
    try:
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the "Know before you go" section
        tips_section = None
        h2_elements = soup.find_all('h2')
        
        for h2 in h2_elements:
            if 'Know before you go' in h2.text:
                tips_section = h2.parent
                break
        
        if not tips_section:
            print(f"No 'Know before you go' section found on {url}")
            return []
        
        # Find the list of tips
        tips_list = tips_section.find('ul', {'class': 'fa-ul'})
        
        if not tips_list:
            print(f"No tips list found in 'Know before you go' section on {url}")
            return []
        
        # Extract the text from each list item
        tips = []
        for li in tips_list.find_all('li'):
            # Remove the SVG icon and get just the text
            tip_text = li.get_text(strip=True)
            if tip_text:
                tips.append(tip_text)
        
        print(f"Found {len(tips)} tips on {url}")
        return tips
    
    except Exception as e:
        print(f"Error extracting tips from {url}: {e}")
        return []

def update_json_with_tips():
    """Update the JSON file with the scraped tips"""
    try:
        # Read the existing JSON file
        with open('hong_kong_bars_precise.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep track of how many entries were updated
        updated_count = 0
        default_count = 0
        error_count = 0
        
        # Update each bar entry with its tips
        total_bars = len(data.get('bars', []))
        for i, bar in enumerate(data.get('bars', [])):
            # Get the detail page URL
            detail_url = bar.get('source_url', '')
            bar_name = bar.get('source_name', 'unknown')
            
            print(f"Processing {i+1}/{total_bars}: {bar_name}")
            
            if detail_url:
                try:
                    # Extract tips from the detail page
                    tips = extract_tips_from_detail_page(detail_url)
                
                    if tips:
                        # Join all tips into a single string with bullet points
                        tips_text = "• " + "\\n• ".join(tips)
                        bar['enrich_localTips'] = tips_text
                        updated_count += 1
                        print(f"Added tips to {bar_name}")
                    else:
                        # Create a default tip for bars without tips
                        default_tip = f"Visit {bar_name} for a unique Hong Kong drinking experience."
                        bar['enrich_localTips'] = default_tip
                        default_count += 1
                        print(f"Added default tip to {bar_name}")
                except Exception as e:
                    error_count += 1
                    print(f"Error processing {bar_name}: {e}")
                    # Create a default tip for bars with errors
                    default_tip = f"Visit {bar_name} for a unique Hong Kong drinking experience."
                    bar['enrich_localTips'] = default_tip
                    default_count += 1
            else:
                # Create a default tip for bars without detail URLs
                default_tip = f"Visit {bar.get('source_name', 'this bar')} for a unique Hong Kong drinking experience."
                bar['enrich_localTips'] = default_tip
                default_count += 1
                print(f"Added default tip to {bar.get('source_name', 'unknown')} (no URL)")
        
        # Write the updated data back to the file
        with open('hong_kong_bars_precise.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSummary: Added actual tips to {updated_count} entries and default tips to {default_count} entries")
        print(f"Errors encountered: {error_count}")
        print(f"Total bars processed: {len(data.get('bars', []))}")
    
    except Exception as e:
        print(f"Error updating JSON file: {e}")

def main():
    print("Starting to scrape tips from Wanderlog detail pages...")
    print("This will take some time as we need to add delays between requests.")
    update_json_with_tips()

if __name__ == "__main__":
    main()

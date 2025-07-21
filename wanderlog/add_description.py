#!/usr/bin/env python3
import json
import requests
import time
import random
import re
from bs4 import BeautifulSoup

# Set up headers to mimic a browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

def extract_about_section(url, max_retries=3):
    """Extract the About section from a bar's detail page and limit to 2 sentences"""
    print(f"Fetching About section from {url}...")
    
    for attempt in range(max_retries):
        try:
            # Add a delay with randomization to be respectful to the server and avoid rate limiting
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
        
        # Look for the "About" section
        about_section = None
        h2_elements = soup.find_all('h2')
        
        for h2 in h2_elements:
            if 'About' in h2.text:
                about_section = h2.parent
                break
        
        if not about_section:
            print(f"No About section found on {url}")
            return ""
        
        # Get the text content after the h2 element
        about_text = ""
        h2_element = about_section.find('h2')
        if h2_element:
            # Get all text after the h2 element
            about_text = h2_element.next_sibling
            
            if not about_text or not about_text.strip():
                # If next_sibling doesn't work, try getting all text and removing the h2 text
                full_text = about_section.get_text()
                h2_text = h2_element.get_text()
                about_text = full_text.replace(h2_text, '', 1).strip()
        
        if not about_text:
            print(f"No About text found on {url}")
            return ""
        
        # Limit to 2 sentences
        sentences = re.split(r'(?<=[.!?])\s+', about_text.strip())
        limited_text = ' '.join(sentences[:2])
        
        print(f"Found About section: {limited_text[:50]}...")
        return limited_text
    
    except Exception as e:
        print(f"Error extracting About section from {url}: {e}")
        return ""

def update_json_with_descriptions():
    """Update the JSON file with the scraped About sections as enrich_description"""
    try:
        # Read the existing JSON file
        with open('hong_kong_bars_precise.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep track of how many entries were updated
        updated_count = 0
        default_count = 0
        error_count = 0
        
        # Update each bar entry with its About section
        total_bars = len(data.get('bars', []))
        for i, bar in enumerate(data.get('bars', [])):
            # Get the detail page URL
            detail_url = bar.get('source_url', '')
            bar_name = bar.get('source_name', 'unknown')
            
            print(f"Processing {i+1}/{total_bars}: {bar_name}")
            
            if detail_url:
                try:
                    # Extract About section from the detail page
                    about_text = extract_about_section(detail_url)
                    
                    if about_text:
                        bar['enrich_description'] = about_text
                        updated_count += 1
                        print(f"Added description to {bar_name}: {about_text[:50]}...")
                    else:
                        # Create a default description for bars without About sections
                        default_description = f"A popular bar in {bar.get('source_neighbourhood', 'Hong Kong')}."
                        bar['enrich_description'] = default_description
                        default_count += 1
                        print(f"Added default description to {bar_name}")
                except Exception as e:
                    error_count += 1
                    print(f"Error processing {bar_name}: {e}")
                    # Create a default description for bars with errors
                    default_description = f"A popular bar in {bar.get('source_neighbourhood', 'Hong Kong')}."
                    bar['enrich_description'] = default_description
                    default_count += 1
            else:
                # Create a default description for bars without detail URLs
                default_description = f"A popular bar in {bar.get('source_neighbourhood', 'Hong Kong')}."
                bar['enrich_description'] = default_description
                default_count += 1
                print(f"Added default description to {bar_name} (no URL)")
        
        # Write the updated data back to the file
        with open('hong_kong_bars_precise.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSummary: Added actual descriptions to {updated_count} entries and default descriptions to {default_count} entries")
        print(f"Errors encountered: {error_count}")
        print(f"Total bars processed: {len(data.get('bars', []))}")
    
    except Exception as e:
        print(f"Error updating JSON file: {e}")

def main():
    print("Starting to scrape About sections from Wanderlog detail pages...")
    print("This will take some time as we need to add delays between requests.")
    update_json_with_descriptions()

if __name__ == "__main__":
    main()

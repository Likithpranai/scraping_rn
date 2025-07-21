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

def extract_menu_items_from_detail_page(url, max_retries=3):
    """Extract menu items from the 'Menu and popular items' section of a bar's detail page"""
    print(f"Fetching menu items from {url}...")
    
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
        
        menu_items = []
        
        # Try to find the menu section using the specific CSS selector
        # First find the parent container
        try:
            parent_container = soup.select_one('#react-main > div:nth-child(2) > div.navbar-offset.container-fixed-padding > div.row.d-flex.flex-row.mt-3 > div.col.col-md-8 > div:nth-child(5)')
            
            if parent_container:
                # Try to find the second carousel slide and extract the span from it
                carousel_slide = parent_container.select_one('div.d-none.d-sm-block > div > div > div > div.slider-frame > div > div:nth-child(2)')
                
                if carousel_slide:
                    # Extract the span text from this slide
                    span = carousel_slide.select_one('span')
                    if span:
                        item_text = span.text.strip()
                        if item_text and item_text != "Menu" and "•" not in item_text:
                            menu_items.append(item_text)
                            print(f"Found menu item using specific selector: {item_text}")
        except Exception as e:
            print(f"Error using specific CSS selector: {e}")
        
        # If we couldn't find anything with the specific selector, try a more general approach
        if not menu_items:
            print("Falling back to general selector approach...")
            # Look for the "Menu and popular items" section
            menu_section = None
            h2_elements = soup.find_all('h2')
            
            for h2 in h2_elements:
                if 'Menu' in h2.text and 'popular items' in h2.text.lower():
                    menu_section = h2.parent
                    break
            
            if menu_section:
                # Find all spans with class "text-muted" within the carousel slides
                slides = menu_section.select('div.slide')
                if slides:
                    for slide in slides:
                        muted_spans = slide.select('span.text-muted')
                        for span in muted_spans:
                            item_text = span.text.strip()
                            if item_text and item_text != "Menu" and "•" not in item_text:
                                menu_items.append(item_text)
                else:
                    # Fallback: look for any text-muted spans within the menu section
                    muted_spans = menu_section.select('span.text-muted')
                    for span in muted_spans:
                        item_text = span.text.strip()
                        if item_text and item_text != "Menu" and "•" not in item_text:
                            menu_items.append(item_text)
        
        print(f"Found {len(menu_items)} menu items on {url}")
        return menu_items
    
    except Exception as e:
        print(f"Error extracting menu items from {url}: {e}")
        return []

def update_json_with_signature_items():
    """Update the JSON file with the scraped menu items as enrich_signature"""
    try:
        # Read the existing JSON file
        with open('hong_kong_bars_precise.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep track of how many entries were updated
        updated_count = 0
        default_count = 0
        error_count = 0
        
        # Update each bar entry with its menu items
        total_bars = len(data.get('bars', []))
        for i, bar in enumerate(data.get('bars', [])):
            # Get the detail page URL
            detail_url = bar.get('source_url', '')
            bar_name = bar.get('source_name', 'unknown')
            
            print(f"Processing {i+1}/{total_bars}: {bar_name}")
            
            if detail_url:
                try:
                    # Extract menu items from the detail page
                    menu_items = extract_menu_items_from_detail_page(detail_url)
                    
                    if menu_items:
                        # Join all menu items into a comma-separated string
                        signature_text = ", ".join(menu_items)
                        bar['enrich_signature'] = signature_text
                        updated_count += 1
                        print(f"Added signature items to {bar_name}: {signature_text}")
                    else:
                        # Create a default signature for bars without menu items
                        default_signature = f"Signature cocktails and drinks"
                        bar['enrich_signature'] = default_signature
                        default_count += 1
                        print(f"Added default signature to {bar_name}")
                except Exception as e:
                    error_count += 1
                    print(f"Error processing {bar_name}: {e}")
                    # Create a default signature for bars with errors
                    default_signature = f"Signature cocktails and drinks"
                    bar['enrich_signature'] = default_signature
                    default_count += 1
            else:
                # Create a default signature for bars without detail URLs
                default_signature = f"Signature cocktails and drinks"
                bar['enrich_signature'] = default_signature
                default_count += 1
                print(f"Added default signature to {bar_name} (no URL)")
        
        # Write the updated data back to the file
        with open('hong_kong_bars_precise.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSummary: Added actual signature items to {updated_count} entries and default signatures to {default_count} entries")
        print(f"Errors encountered: {error_count}")
        print(f"Total bars processed: {len(data.get('bars', []))}")
    
    except Exception as e:
        print(f"Error updating JSON file: {e}")

def main():
    print("Starting to scrape menu items from Wanderlog detail pages...")
    print("This will take some time as we need to add delays between requests.")
    update_json_with_signature_items()

if __name__ == "__main__":
    main()

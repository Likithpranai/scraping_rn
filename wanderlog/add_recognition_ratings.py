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

def extract_rating_from_detail_page(url, max_retries=3):
    """Extract rating information from a bar's detail page"""
    print(f"Fetching rating from {url}...")
    
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
        
        # Look for the rating div with stars and rating value
        rating_div = soup.find('div', class_='d-flex flex-wrap align-items-center')
        
        if not rating_div:
            print(f"No rating div found on {url}")
            return None
        
        # Find the rating value (usually in a span with font-weight-bold)
        rating_span = rating_div.find('span', class_='font-weight-bold')
        
        if not rating_span:
            print(f"No rating value found in rating div on {url}")
            return None
        
        rating = rating_span.text.strip()
        
        # Find the number of reviews in parentheses
        reviews_text = rating_div.find('span', class_='text-muted')
        reviews_count = "0"
        
        if reviews_text:
            # Extract just the number from the text like "(257)"
            reviews_match = re.search(r'\((\d+)\)', reviews_text.text)
            if reviews_match:
                reviews_count = reviews_match.group(1)
        
        # Combine rating and review count
        rating_info = f"{rating} ({reviews_count} reviews)"
        print(f"Found rating: {rating_info} on {url}")
        return rating_info
    
    except Exception as e:
        print(f"Error extracting rating from {url}: {e}")
        return None

def update_json_with_ratings():
    """Update the JSON file with the scraped ratings"""
    try:
        # Read the existing JSON file
        with open('hong_kong_bars_precise.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Keep track of how many entries were updated
        updated_count = 0
        default_count = 0
        error_count = 0
        
        # Update each bar entry with its rating
        total_bars = len(data.get('bars', []))
        for i, bar in enumerate(data.get('bars', [])):
            # Get the detail page URL
            detail_url = bar.get('source_url', '')
            bar_name = bar.get('source_name', 'unknown')
            
            print(f"Processing {i+1}/{total_bars}: {bar_name}")
            
            if detail_url:
                try:
                    # Extract rating from the detail page
                    rating = extract_rating_from_detail_page(detail_url)
                    
                    if rating:
                        bar['enrich_recognition'] = rating
                        updated_count += 1
                        print(f"Added rating to {bar_name}")
                    else:
                        # Create a default rating for bars without ratings
                        default_rating = "Not rated"
                        bar['enrich_recognition'] = default_rating
                        default_count += 1
                        print(f"Added default rating to {bar_name}")
                except Exception as e:
                    error_count += 1
                    print(f"Error processing {bar_name}: {e}")
                    # Create a default rating for bars with errors
                    default_rating = "Not rated"
                    bar['enrich_recognition'] = default_rating
                    default_count += 1
            else:
                # Create a default rating for bars without detail URLs
                default_rating = "Not rated"
                bar['enrich_recognition'] = default_rating
                default_count += 1
                print(f"Added default rating to {bar_name} (no URL)")
        
        # Write the updated data back to the file
        with open('hong_kong_bars_precise.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSummary: Added actual ratings to {updated_count} entries and default ratings to {default_count} entries")
        print(f"Errors encountered: {error_count}")
        print(f"Total bars processed: {len(data.get('bars', []))}")
    
    except Exception as e:
        print(f"Error updating JSON file: {e}")

def main():
    print("Starting to scrape ratings from Wanderlog detail pages...")
    print("This will take some time as we need to add delays between requests.")
    update_json_with_ratings()

if __name__ == "__main__":
    main()

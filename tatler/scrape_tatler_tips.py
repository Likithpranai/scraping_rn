#!/usr/bin/env python3
import json
import requests
from bs4 import BeautifulSoup
import time
import re

def extract_tatler_tip(url):
    """
    Extract the Tatler Tip from a restaurant detail page.
    Returns the tip text or None if not found.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the Tatler Tip section
        # First try to find h3 with "Tatler Tip" text
        tip_header = soup.find('h3', string=re.compile(r'Tatler\s+Tip', re.IGNORECASE))
        
        if tip_header:
            # Get the next paragraph after the h3
            tip_content = tip_header.find_next('p')
            if tip_content:
                return tip_content.get_text().strip()
        
        # Alternative approach: look for div with rich-text class containing Tatler Tip
        rich_text_divs = soup.find_all('div', class_='rich-text')
        for div in rich_text_divs:
            if div.find('h3', string=re.compile(r'Tatler\s+Tip', re.IGNORECASE)):
                tip_content = div.find('h3', string=re.compile(r'Tatler\s+Tip', re.IGNORECASE)).find_next('p')
                if tip_content:
                    return tip_content.get_text().strip()
        
        return None
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def extract_must_try_dishes(url):
    """
    Extract the 'Must Try' dishes from a restaurant detail page.
    Returns a list of dishes or None if not found.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the Must Try section
        # First try to find the heading with "Must Try" text
        must_try_heading = soup.find('p', string=re.compile(r'Must\s+Try', re.IGNORECASE), class_=lambda c: c and 'text-primary-color' in c)
        
        if must_try_heading:
            # Find the parent div that contains the Must Try section
            must_try_section = must_try_heading.find_parent('div')
            if must_try_section:
                # Find the ul with class 'must-try'
                must_try_list = must_try_section.find('ul', class_='must-try')
                if must_try_list:
                    # Get all list items
                    dishes = [li.get_text().strip() for li in must_try_list.find_all('li')]
                    return dishes
        
        # Alternative approach: look for ul with class 'must-try'
        must_try_list = soup.find('ul', class_='must-try')
        if must_try_list:
            dishes = [li.get_text().strip() for li in must_try_list.find_all('li')]
            return dishes
        
        return None
    except Exception as e:
        print(f"Error scraping must-try dishes from {url}: {e}")
        return None

def extract_description(url):
    """
    Extract the short description from a restaurant detail page.
    Returns the first 20 words of the description or None if not found.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the description paragraph with specific class
        description_p = soup.find('p', class_=lambda c: c and 'font-gt-america' in c and 'font-weight--700' in c and 'text-primary-color-100' in c)
        
        if description_p:
            full_text = description_p.get_text().strip()
            # Get the first 20 words
            words = full_text.split()
            if len(words) > 20:
                return ' '.join(words[:20])
            return full_text
        
        # Alternative approach: look for the first paragraph in the content container
        content_container = soup.select_one('#main-content > div > div > div > div.mx-16.tablet\\:mx-48 > div > div.content-container > div > div > div:nth-child(1)')
        if content_container:
            description_p = content_container.find('p', class_=lambda c: c and 'font-gt-america' in c)
            if description_p:
                full_text = description_p.get_text().strip()
                # Get the first 20 words
                words = full_text.split()
                if len(words) > 20:
                    return ' '.join(words[:20])
                return full_text
        
        return None
    except Exception as e:
        print(f"Error scraping description from {url}: {e}")
        return None

def main():
    # Load the JSON file
    with open('tatler_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Track changes
    tips_found = 0
    signature_dishes_found = 0
    descriptions_found = 0
    
    # Process each restaurant entry
    for i, entry in enumerate(data):
        # Skip non-restaurant entries (those without source_url or with empty source_url)
        if 'source_url' not in entry or not entry['source_url']:
            continue
            
        url = entry['source_url']
        
        # Skip entries that don't look like restaurant pages
        if 'dining/' not in url:
            continue
            
        print(f"Processing {i+1}/{len(data)}: {entry.get('source_name', 'Unknown')}")
        
        # Extract the Tatler Tip if not already present
        if 'enrich_localTips' not in entry:
            tip = extract_tatler_tip(url)
            
            if tip:
                entry['enrich_localTips'] = tip
                tips_found += 1
                print(f"  ✓ Tip found: {tip[:50]}...")
            else:
                print(f"  ✗ No tip found")
        
        # Extract the Must Try dishes if not already present
        if 'enrich_signature' not in entry:
            dishes = extract_must_try_dishes(url)
            
            if dishes and len(dishes) > 0:
                entry['enrich_signature'] = dishes
                signature_dishes_found += 1
                print(f"  ✓ Signature dishes found: {len(dishes)}")
            else:
                print(f"  ✗ No signature dishes found")
        
        # Extract the description
        description = extract_description(url)
        
        if description:
            entry['enrich_description'] = description
            descriptions_found += 1
            print(f"  ✓ Description found: {description[:50]}...")
        else:
            print(f"  ✗ No description found")
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(1)
    
    # Save the updated JSON file
    with open('tatler_results.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nSummary: Found tips for {tips_found} new entries")
    print(f"Summary: Found signature dishes for {signature_dishes_found} new entries")
    print(f"Summary: Found descriptions for {descriptions_found} out of {len(data)} entries")

if __name__ == "__main__":
    main()

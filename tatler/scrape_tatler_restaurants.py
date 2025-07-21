#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

# Constants
BASE_URL = "https://www.tatlerasia.com"
LISTING_URL = "https://www.tatlerasia.com/list/best-restaurants-hong-kong?filter_3%5B%5D=2025&page=1"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tatler_results.json")
REQUEST_DELAY = 0.5  # Delay between requests in seconds

def get_restaurant_listings() -> List[Dict[str, Any]]:
    print(f"\nFetching restaurant listings from {LISTING_URL}...")
    
    try:
        response = requests.get(LISTING_URL, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        restaurant_items = []
        
        # First try to find all h2 elements that are likely restaurant names
        h2_elements = soup.find_all('h2', class_=lambda c: c and 'heading-xl' in c)
        
        for h2 in h2_elements:
            # For each h2, find its parent div that contains the whole card
            parent_div = h2.find_parent('div')
            if parent_div:
                restaurant_items.append(parent_div)
        
        if not restaurant_items:
            # Try alternative approach if the above doesn't work
            restaurant_items = soup.select('div > a[href^="/dining/"]')
            if not restaurant_items:
                # Try another approach - find all divs containing restaurant links
                all_divs = soup.find_all('div')
                restaurant_items = [div for div in all_divs if div.find('a', href=lambda h: h and h.startswith('/dining/'))]
        
        print(f"Found {len(restaurant_items)} restaurant items")
        
        restaurants = []
        for item in restaurant_items:
            restaurant_data = {
                "source_url": "",
                "source_name": "",
                "source_address": "",
                "source_neighbourhood": "",
                "source_pricepoint": "",
                "source_photoUrls": [],
                "source_categories": []
            }
            
            # Extract source_url from the link in the card that points to the restaurant detail page
            # First, find the h2 element (restaurant name)
            name_element = item.find('h2', class_=lambda c: c and 'heading-xl' in c)
            if name_element:
                # Find the parent anchor tag that wraps the h2
                link_element = name_element.find_parent('a')
                if link_element and link_element.has_attr('href'):
                    href = link_element.get('href', '')
                    if href:
                        restaurant_data["source_url"] = f"{BASE_URL}{href}"
                else:
                    # If no parent anchor, look for any anchor with dining URL in the same div
                    link_element = item.find('a', href=lambda h: h and '/dining/' in h)
                    if link_element:
                        href = link_element.get('href', '')
                        if href:
                            restaurant_data["source_url"] = f"{BASE_URL}{href}"
            
            # Extract source_name from h2 tag
            name_element = item.find('h2', class_=lambda c: c and 'heading-xl' in c)
            if name_element:
                restaurant_data["source_name"] = name_element.text.strip()
            
            # Extract source_photoUrls from img tag
            img_element = item.find('img', {'data-src': True}) or item.find('img', {'src': True})
            if img_element:
                img_url = img_element.get('data-src') or img_element.get('src')
                if img_url and img_url.startswith('http') and 'tatler-placeholder.svg' not in img_url:
                    restaurant_data["source_photoUrls"].append(img_url)
            
            # Extract source_neighbourhood from p tag
            neighbourhood_element = item.find('p', class_=lambda c: c and 'caption-s' in c and 'text-opacity-50' in c)
            if neighbourhood_element:
                restaurant_data["source_neighbourhood"] = neighbourhood_element.text.strip()
            
            # Extract source_categories from p tag
            categories_element = item.find('p', class_=lambda c: c and 'uppercase' in c and 'eyebrow-s' in c)
            if categories_element:
                restaurant_data["source_categories"] = [categories_element.text.strip()]
            
            if restaurant_data["source_name"]:  # Only add if we found a name
                print(f"Found restaurant: {restaurant_data['source_name']}")
                restaurants.append(restaurant_data)
        
        return restaurants
        
    except Exception as e:
        print(f"Error fetching restaurant listings: {e}")
        return []

def extract_address(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract address from the restaurant detail page.
    
    Args:
        soup: BeautifulSoup object of the detail page
        
    Returns:
        Address string or None if not found
    """
    # Find the information container
    information_container = soup.find('div', class_=lambda c: c and 'information-container' in c)
    if information_container:
        # Find the address section
        address_section = information_container.find('p', class_='font-weight--700', string=lambda s: s and 'Address' in s)
        if address_section:
            address_element = address_section.find_next('a')
            if address_element:
                return address_element.text.strip()
    return None

def extract_price_point(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract price point from the restaurant detail page.
    
    Args:
        soup: BeautifulSoup object of the detail page
        
    Returns:
        Price point string or None if not found
    """
    # Find the information container
    information_container = soup.find('div', class_=lambda c: c and 'information-container' in c)
    if information_container:
        # Find the price section
        price_section = information_container.find('p', class_='font-weight--700', string=lambda s: s and 'Price' in s)
        if price_section:
            price_parent = price_section.find_parent('div')
            if price_parent:
                price_spans = price_parent.find_all('span', class_='text-primary-color-70')
                if price_spans:
                    return '$' * len(price_spans)
    return None

def extract_awards(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Extract awards and recognition information from the restaurant detail page.
    
    Args:
        soup: BeautifulSoup object of the detail page
        
    Returns:
        List of award dictionaries with year and award name
    """
    awards = []
    
    # Find the awards section
    awards_section = soup.find('div', class_='mt-32 tablet:mt-48', attrs={'style': lambda s: s and '--color:201,169,111;' in s})
    
    if not awards_section:
        # Try alternative selector
        awards_section = soup.find('div', string=lambda s: s and 'Awards' in s)
        if awards_section:
            awards_section = awards_section.find_parent('div')
    
    if awards_section:
        # Find the award container
        award_container = awards_section.find('div', class_='award-container')
        
        if award_container:
            # Get all paragraphs in the award container
            paragraphs = award_container.find_all('p', class_=lambda c: c and 'text-body-base' in c)
            
            # Process paragraphs in pairs (year and award name)
            for i in range(0, len(paragraphs) - 1, 2):
                if i + 1 < len(paragraphs):
                    year = paragraphs[i].text.strip()
                    award_name = paragraphs[i + 1].text.strip()
                    
                    if year and award_name:
                        awards.append({
                            "year": year,
                            "award": award_name
                        })
    
    return awards

def extract_additional_photos(soup: BeautifulSoup) -> List[str]:
    """
    Extract additional photo URLs from the restaurant detail page.
    
    Args:
        soup: BeautifulSoup object of the detail page
        
    Returns:
        List of photo URLs
    """
    photo_urls = []
    
    # Try multiple possible containers
    photo_containers = [
        soup.find('div', class_=lambda c: c and 'grid-container' in c),
        soup.find('div', class_=lambda c: c and 'gallery' in c),
        soup.find('div', class_=lambda c: c and 'image-gallery' in c)
    ]
    
    for photo_container in photo_containers:
        if not photo_container:
            continue
            
        # Try different approaches to find images
        # 1. Look for div elements with square-image class
        photo_divs = photo_container.find_all('div', class_=lambda c: c and 'square-image' in c)
        
        # 2. If no square-image divs, try to find pictures directly
        if not photo_divs:
            photo_divs = photo_container.find_all('picture')
        
        # 3. If still no luck, try to find images directly
        if not photo_divs:
            img_elements = photo_container.find_all('img', {'data-src': True}) or \
                          photo_container.find_all('img', {'src': True})
            
            for img in img_elements:
                # Skip placeholder images
                img_url = img.get('data-src') or img.get('src')
                if img_url and img_url.startswith('http') and 'tatler-placeholder.svg' not in img_url:
                    photo_urls.append(img_url)
            
            continue  # Skip the rest of the loop for this container
        
        # Process photo divs (either square-image divs or picture elements)
        for div in photo_divs:
            # Find the picture element and then the img inside it
            picture_element = div if div.name == 'picture' else div.find('picture')
            if picture_element:
                img_element = picture_element.find('img', {'data-src': True}) or picture_element.find('img', {'src': True})
                if img_element:
                    # Skip placeholder images
                    if 'tatler-placeholder.svg' in (img_element.get('src', '') or img_element.get('data-src', '')):
                        continue
                    
                    # Get the image URL
                    img_url = img_element.get('data-src') or img_element.get('src')
                    if img_url and img_url.startswith('http'):
                        photo_urls.append(img_url)
    
    return photo_urls

def extract_restaurant_details(restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract additional details from the restaurant detail page.
    
    Args:
        restaurant_data: Initial restaurant data dictionary
        
    Returns:
        Updated restaurant data dictionary
    """
    url = restaurant_data.get('source_url', '')
    name = restaurant_data.get('source_name', '')
    
    if not url:
        print(f"No URL found for restaurant {name}")
        return restaurant_data
    
    print(f"\nExtracting details for {name} from {url}...")
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract address
        address = extract_address(soup)
        if address:
            restaurant_data['source_address'] = address
            print(f"  Address: {address}")
        
        # Extract price point
        price_point = extract_price_point(soup)
        if price_point:
            restaurant_data['source_pricepoint'] = price_point
            print(f"  Price Point: {price_point}")
        
        # Extract awards and recognition
        awards = extract_awards(soup)
        if awards:
            restaurant_data['enrich_recognition'] = awards
            print(f"  Awards: {len(awards)} found")
        else:
            restaurant_data['enrich_recognition'] = []
        
        # Add enrich_localname and enrich_english_name
        restaurant_data['enrich_localname'] = restaurant_data.get('source_name', '')
        restaurant_data['enrich_english_name'] = restaurant_data.get('source_name', '')
        
        # Extract additional photos
        additional_photos = extract_additional_photos(soup)
        if additional_photos:
            # Combine with existing photos, ensuring no duplicates
            existing_photos = restaurant_data.get('source_photoUrls', [])
            all_photos = list(set(existing_photos + additional_photos))
            restaurant_data['source_photoUrls'] = all_photos
            print(f"  Photos: {len(all_photos)} found")
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"  Detail page not found (404). Using data from listing page only.")
            # Set default values for missing fields
            if 'source_address' not in restaurant_data or not restaurant_data['source_address']:
                restaurant_data['source_address'] = ""
            if 'source_pricepoint' not in restaurant_data or not restaurant_data['source_pricepoint']:
                restaurant_data['source_pricepoint'] = "$$$$"  # Assuming high-end restaurants
        else:
            print(f"Error extracting restaurant details: {e}")
    except Exception as e:
        print(f"Error extracting restaurant details: {e}")
    
    return restaurant_data

def save_results(restaurants: List[Dict[str, Any]]) -> None:
    """
    Save restaurant data to JSON file.
    
    Args:
        restaurants: List of restaurant data dictionaries
    """
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(restaurants, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(restaurants)} restaurants to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving results: {e}")

def main():
    """
    Main function to run the scraper.
    """
    print("Starting Tatler Asia restaurant scraper...")
    
    # Get restaurant listings from the main page
    restaurants = get_restaurant_listings()
    
    # Extract additional details for each restaurant
    for i, restaurant in enumerate(restaurants):
        print(f"\nProcessing restaurant {i+1}/{len(restaurants)}")
        # Add a delay between requests to be polite
        if i > 0:
            time.sleep(REQUEST_DELAY)
        
        # Extract details from the restaurant page
        restaurants[i] = extract_restaurant_details(restaurant)
    
    # Save results to JSON file
    save_results(restaurants)
    
    print("\nScraping completed!")

if __name__ == "__main__":
    main()

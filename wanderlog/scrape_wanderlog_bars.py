#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wanderlog Bar Scraper
---------------------
This script scrapes information about the best bars and drinks in Hong Kong from Wanderlog.
URL: https://wanderlog.com/list/geoCategory/685/best-bars-and-drinks-in-hong-kong
"""

import json
import time
import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Any, Optional
import os
import asyncio
from playwright.async_api import async_playwright

# Constants
URL = "https://wanderlog.com/list/geoCategory/685/best-bars-and-drinks-in-hong-kong"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
OUTPUT_FILE = "wanderlog_bars.json"
REQUEST_DELAY = 0.5  # Delay between requests in seconds

def fetch_page(url: str) -> Optional[BeautifulSoup]:
    """
    Fetch the HTML content of a page and return a BeautifulSoup object.
    
    Args:
        url: The URL to fetch.
        
    Returns:
        BeautifulSoup object or None if the request fails.
    """
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


async def fetch_page_with_playwright(url: str) -> Optional[BeautifulSoup]:
    """
    Fetch the HTML content of a page using Playwright and return a BeautifulSoup object.
    This is necessary for JavaScript-rendered content.
    
    Args:
        url: The URL to fetch.
        
    Returns:
        BeautifulSoup object or None if the request fails.
    """
    try:
        async with async_playwright() as p:
            # Launch a browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=HEADERS['User-Agent'],
                viewport={'width': 1920, 'height': 1080}  # Set a larger viewport to ensure content loads
            )
            
            # Open a new page
            page = await context.new_page()
            
            # Navigate to the URL with longer timeout
            print("Navigating to URL and waiting for network idle...")
            await page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Wait for initial content to load
            print("Initial page loaded, waiting for content to render...")
            await asyncio.sleep(2)
            
            # Scroll down to load more content (lazy loading)
            print("Scrolling to load more content...")
            for i in range(15):  # Increased scroll attempts
                await page.evaluate('window.scrollBy(0, 800)')
                await asyncio.sleep(1)
                if i % 5 == 0:
                    print(f"Scrolled {i+1} times...")
            
            # Wait for the content to load - try different selectors
            print("Waiting for bar card elements to appear...")
            try:
                await page.wait_for_selector("div[role='button']", timeout=10000)
                print("Found div[role='button'] elements")
            except Exception:
                print("Waiting for alternative selectors...")
                try:
                    await page.wait_for_selector("h2.font-weight-bold", timeout=10000)
                    print("Found h2.font-weight-bold elements")
                except Exception:
                    print("Could not find expected selectors, continuing anyway...")
            
            # Allow additional time for all elements to render
            print("Waiting for final rendering...")
            await asyncio.sleep(10)
            
            # Get the page source and parse it with BeautifulSoup
            print("Capturing page content...")
            content = await page.content()
            
            # Take a screenshot for debugging
            await page.screenshot(path="wanderlog_screenshot.png")
            print("Screenshot saved as wanderlog_screenshot.png")
            
            await browser.close()
            print("Browser closed")
            
            return BeautifulSoup(content, "html.parser")
    
    except Exception as e:
        print(f"Error fetching {url} with Playwright: {e}")
        return None

def extract_bar_cards(soup: BeautifulSoup) -> List[BeautifulSoup]:
    """
    Extract all bar card elements from the page.
    
    Args:
        soup: BeautifulSoup object of the page.
        
    Returns:
        List of BeautifulSoup objects representing bar cards.
    """
    # Try multiple approaches to find bar cards
    bar_cards = []
    
    # Approach 1: Look for div elements with role="button" and the exact classes from the provided HTML
    cards1 = soup.find_all("div", {
        "role": "button", 
        "class": lambda c: c and all(cls in c for cls in ["cursor-pointer", "clearfix", "BoardPlaceView__selected", "PlaceView__selectable"]) if c else False
    })
    if cards1:
        bar_cards.extend(cards1)
        print(f"Found {len(cards1)} cards using approach 1 (exact class match)")
    
    # Approach 2: Look for div elements with role="button" and partial class match
    if len(bar_cards) < 5:  # If we found few cards, try a more relaxed approach
        cards2 = soup.find_all("div", {
            "role": "button", 
            "class": lambda c: c and "BoardPlaceView__selected" in c if c else False
        })
        new_cards = [card for card in cards2 if card not in bar_cards]
        if new_cards:
            print(f"Found {len(new_cards)} additional cards using approach 2 (partial class match)")
            bar_cards.extend(new_cards)
    
    # Approach 3: Look for any div with role="button" that contains h2 with a link
    if len(bar_cards) < 5:
        cards3 = soup.find_all("div", {"role": "button"})
        new_cards = [card for card in cards3 if card.find("h2") and card.find("a") and card not in bar_cards]
        if new_cards:
            print(f"Found {len(new_cards)} additional cards using approach 3 (role=button with h2 and link)")
            bar_cards.extend(new_cards)
    
    # Approach 4: Look for h2 elements with a class containing "font-weight-bold" and a link
    if len(bar_cards) < 5:
        h2_elements = soup.find_all("h2", class_=lambda c: c and "font-weight-bold" in c if c else False)
        for h2 in h2_elements:
            if h2.find("a"):
                # Go up to find the parent card div
                parent = h2.parent
                while parent and parent.name == "div":
                    if parent.get("role") == "button":
                        if parent not in bar_cards:
                            bar_cards.append(parent)
                            break
                    parent = parent.parent
        if len(bar_cards) > 0:
            print(f"Found {len(bar_cards)} cards using approach 4 (h2 with font-weight-bold)")
    
    # Approach 5: Direct search for h2 elements with links
    if len(bar_cards) < 5:
        h2_with_links = []
        for h2 in soup.find_all("h2"):
            if h2.find("a", href=True):
                h2_with_links.append(h2)
        
        print(f"Found {len(h2_with_links)} h2 elements with links")
        
        # For each h2 with a link, try to find its parent bar card
        for h2 in h2_with_links:
            parent = h2.parent
            while parent and parent.name == "div":
                if "class" in parent.attrs and any(cls in parent.get("class", []) for cls in ["PlaceView__", "BoardPlaceView__"]):
                    if parent not in bar_cards:
                        bar_cards.append(parent)
                        break
                parent = parent.parent
    
    # Remove duplicates
    unique_cards = []
    card_strings = set()
    for card in bar_cards:
        card_str = str(card)
        if card_str not in card_strings:
            card_strings.add(card_str)
            unique_cards.append(card)
    
    print(f"Found {len(unique_cards)} unique bar cards after deduplication")
    return unique_cards

def extract_bar_info(card: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract information from a bar card based on the provided HTML structure.
    Focus only on the required fields specified by the user.
    
    Args:
        card: BeautifulSoup object representing a bar card.
        
    Returns:
        Dictionary containing bar information.
    """
    bar_info = {
        "source_name": "",
        "source_url": "",
        "source_address": "",  # Will be scraped or filled via perplexity
        "source_neighbourhood": "",  # Will be derived from address via cerebras
        "source_pricepoint": "",  # Will be scraped or filled via cerebras/perplexity
        "source_photoUrls": [],
        "source_categories": []
    }
    
    # Extract name and URL (100% scrapable)
    name_element = card.find("h2", class_=lambda c: c and "font-weight-bold" in c if c else False)
    if name_element and name_element.find("a"):
        a_tag = name_element.find("a")
        bar_info["source_name"] = a_tag.get_text(strip=True)
        
        # Extract URL (100% scrapable)
        if a_tag.get("href"):
            relative_url = a_tag.get("href")
            bar_info["source_url"] = f"https://wanderlog.com{relative_url}" if relative_url.startswith("/") else relative_url
    else:
        # Fallback: try any h2 with a link
        h2_element = card.find("h2")
        if h2_element and h2_element.find("a"):
            a_tag = h2_element.find("a")
            bar_info["source_name"] = a_tag.get_text(strip=True)
            
            if a_tag.get("href"):
                relative_url = a_tag.get("href")
                bar_info["source_url"] = f"https://wanderlog.com{relative_url}" if relative_url.startswith("/") else relative_url
    
    # Extract address if available (scraped OR perplexity)
    # Based on the HTML structure, the address might be in a div with class text-muted
    # but not part of the ratings section
    
    # First, try to find a description div that might contain the address
    description_div = card.find("div", class_=lambda c: c and "mt-2" in c if c else False)
    if description_div and not description_div.find("div", class_="badge"):
        # This might be the description text which sometimes contains the address
        description_text = description_div.get_text(strip=True)
        if description_text and not description_text.startswith("Mentioned on"):
            # This might be a description, not an address, but we'll store it for now
            bar_info["source_address"] = description_text
    
    # If we didn't find an address, look for other text-muted divs
    if not bar_info["source_address"]:
        # Exclude divs that are part of the rating section or contain "Mentioned on"
        for div in card.find_all("div", class_=lambda c: c and "text-muted" in c if c else False):
            text = div.get_text(strip=True)
            if text and not text.startswith("(") and not "reviews" in text.lower() and not "Mentioned on" in text:
                bar_info["source_address"] = text
                break
    
    # Extract price point (range or exact) from badge elements
    price_badges = card.find_all("div", class_=lambda c: c and "Badge__" in c and "badge" in c.lower() if c else False)
    for badge in price_badges:
        badge_text = badge.get_text(strip=True)
        if "$" in badge_text:
            bar_info["source_pricepoint"] = badge_text
            break
    
    # Extract categories from badge elements (excluding price badges)
    categories = []
    for badge in card.find_all("div", class_=lambda c: c and "Badge__" in c and "badge" in c.lower() if c else False):
        badge_text = badge.get_text(strip=True)
        if not "$" in badge_text:  # Skip price badges
            categories.append(badge_text)
    
    if categories:
        bar_info["source_categories"] = categories
    
    # Extract image URLs from the carousel images
    image_urls = []
    
    # Look for images in the carousel
    carousel = card.find("div", class_="Carousel")
    if carousel:
        # Find all images with object-fit-cover class
        img_elements = carousel.find_all("img", class_="object-fit-cover")
        for img in img_elements:
            # Check src attribute
            if img.get("src") and not img.get("src").startswith("data:"):
                image_urls.append(img.get("src"))
            
            # Check srcset attribute
            if img.get("srcset"):
                srcset_urls = img.get("srcset").split(",")
                for srcset_url in srcset_urls:
                    url = srcset_url.strip().split(" ")[0]
                    if url and not url.startswith("data:"):
                        image_urls.append(url)
    
    # If no images found in carousel, try to find any images in the card
    if not image_urls:
        for img in card.find_all("img"):
            if img.get("src") and not img.get("src").startswith("data:") and not "base64" in img.get("src"):
                image_urls.append(img.get("src"))
            elif img.get("srcset"):
                srcset_urls = img.get("srcset").split(",")
                for srcset_url in srcset_urls:
                    url = srcset_url.strip().split(" ")[0]
                    if url and not url.startswith("data:") and not "base64" in url:
                        image_urls.append(url)
    
    # Filter out duplicates and base64 images
    image_urls = [url for url in image_urls if url and not url.startswith("data:") and not "base64" in url]
    if image_urls:
        bar_info["source_photoUrls"] = list(set(image_urls))
    
    return bar_info

async def scrape_wanderlog_bars() -> List[Dict[str, Any]]:
    """
    Main function to scrape Wanderlog bars.
    
    Returns:
        List of dictionaries containing bar information.
    """
    print(f"Starting Wanderlog bar scraper...")
    print(f"Fetching bar listings from {URL} using Playwright...")
    
    soup = await fetch_page_with_playwright(URL)
    if not soup:
        print("Failed to fetch the page with Playwright. Exiting.")
        return []
    
    # Save the HTML for debugging if needed
    with open("wanderlog_page.html", "w", encoding="utf-8") as f:
        f.write(str(soup))
    print("Saved HTML to wanderlog_page.html for debugging")
    
    # Try different approaches to find the main content area
    main_content = None
    
    # Approach 1: Look for PlacesList__ class
    main_content = soup.find("div", class_=lambda c: c and "PlacesList__" in c if c else False)
    if main_content:
        print("Found main content area using PlacesList__ class")
    
    # Approach 2: Look for a container with multiple bar cards
    if not main_content:
        # Find all divs with role="button" that might be bar cards
        potential_cards = soup.find_all("div", {"role": "button"})
        if potential_cards:
            # Find a common parent that contains multiple cards
            for card in potential_cards:
                parent = card.parent
                while parent and parent.name == "div":
                    siblings = parent.find_all("div", {"role": "button"}, recursive=False)
                    if len(siblings) > 1:
                        main_content = parent
                        print(f"Found main content area containing {len(siblings)} potential cards")
                        break
                    parent = parent.parent
                if main_content:
                    break
    
    # Extract bar cards from the main content or the entire page
    if main_content:
        bar_cards = extract_bar_cards(main_content)
    else:
        print("Could not find main content area, searching in entire page")
        bar_cards = extract_bar_cards(soup)
    
    if not bar_cards:
        print("No bar cards found using standard extraction. Trying direct h2 extraction...")
        # Last resort: Extract directly from h2 elements with links
        h2_elements = soup.find_all("h2")
        bars = []
        
        for i, h2 in enumerate(h2_elements):
            a_tag = h2.find("a", href=True)
            if a_tag:
                print(f"Found h2 with link: {a_tag.get_text(strip=True)}")
                bar_info = {
                    "source_name": h2.get_text(strip=True),
                    "source_url": "",
                    "source_address": "",
                    "source_neighbourhood": "",
                    "source_pricepoint": "",
                    "source_photoUrls": [],
                    "source_categories": []
                }
                
                # Extract URL
                a_tag = h2.find("a")
                if a_tag and a_tag.get("href"):
                    relative_url = a_tag.get("href")
                    bar_info["source_url"] = f"https://wanderlog.com{relative_url}" if relative_url.startswith("/") else relative_url
                
                print(f"Found bar via direct extraction: {bar_info['source_name']}")
                bars_data.append(bar_info)
    
    return bars_data

def save_to_json(data: List[Dict[str, Any]], filename: str) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: List of dictionaries to save.
        filename: Name of the output file.
    """
    # Filter out empty entries
    filtered_data = [item for item in data if item.get("source_name")]
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(filtered_data)} bars to {filename}")

async def main_async():
    """Asynchronous main entry point of the script."""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    bars_data = await scrape_wanderlog_bars()
    if bars_data:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
        save_to_json(bars_data, output_path)
        print("Scraping completed!")
    else:
        print("No data was scraped.")

def main():
    """Main entry point of the script."""
    asyncio.run(main_async())

if __name__ == "__main__":
    main()

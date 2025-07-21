#!/usr/bin/env python3
"""
Wanderlog Bar Scraper - Detailed View Approach
This script extracts bar information from Wanderlog's "Best Bars and Drinks in Hong Kong" page
by navigating through the detailed view of each bar.
"""

import asyncio
import json
import os
from typing import Dict, List, Any, Optional

from playwright.async_api import async_playwright, Page

# Constants
URL = "https://wanderlog.com/list/geoCategory/685/best-bars-and-drinks-in-hong-kong"
OUTPUT_FILE = "wanderlog_bars_detailed.json"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
}

async def extract_bar_info(page: Page) -> Dict[str, Any]:
    """
    Extract information from the detailed view of a bar.
    
    Args:
        page: Playwright page object with the bar's detailed view open
        
    Returns:
        Dictionary containing bar information
    """
    bar_info = {
        "source_name": "",
        "source_url": page.url,
        "source_address": "",
        "source_neighbourhood": "",  # Will be derived from address via cerebras
        "source_pricepoint": "",
        "source_photoUrls": [],
        "source_categories": []
    }
    
    try:
        # Extract bar name
        name_element = await page.query_selector("div.ml-2 strong")
        if name_element:
            bar_info["source_name"] = await name_element.text_content()
            print(f"Found bar name: {bar_info['source_name']}")
        
        # Extract address - more specific selector based on user's HTML
        address_locator = "div.IconRow:has(svg[data-icon='location-dot']) div.col.p-0.minw-0"
        address_element = await page.query_selector(address_locator)
        if address_element:
            address_text = await address_element.text_content()
            # Clean up the address text (remove any 'Mentioned on' text)
            if "Mentioned on" in address_text:
                address_text = address_text.split("Mentioned on")[0].strip()
            bar_info["source_address"] = address_text
            print(f"Found address: {bar_info['source_address']}")
        
        # Extract price point
        price_element = await page.query_selector("div.badge:has(span.text-muted)")
        if price_element:
            bar_info["source_pricepoint"] = await price_element.text_content()
            print(f"Found price point: {bar_info['source_pricepoint']}")
        
        # Extract categories - using exact selector provided by user
        # Target the specific div.mb-2 in the card
        category_container = await page.query_selector("div.pt-2 > div.mb-2")
        categories = []
        
        if category_container:
            # Get all badge elements within this container
            category_elements = await category_container.query_selector_all("div.badge.Badge__lightGray")
            for element in category_elements:
                category_text = await element.text_content()
                if category_text and "$" not in category_text:  # Exclude price badges
                    categories.append(category_text)
            
            print(f"Found {len(category_elements)} category elements")
        else:
            print("Category container not found")
        
        if categories:
            bar_info["source_categories"] = categories
            print(f"Found categories: {bar_info['source_categories']}")
        
        # Extract image URLs - limit to main images only
        # First try to get the main image from the ImageButton
        main_img = await page.query_selector("div.ImageButton__button img.object-fit-cover")
        image_urls = []
        
        if main_img:
            src = await main_img.get_attribute("src")
            if src and not src.startswith("data:"):
                image_urls.append(src)
                print(f"Found main image: {src}")
        
        # If no main image found or we want a few more, get up to 2 additional images
        if len(image_urls) < 3:
            additional_imgs = await page.query_selector_all("img.object-fit-cover")
            for img in additional_imgs:
                if len(image_urls) >= 3:  # Limit to 3 images total
                    break
                src = await img.get_attribute("src")
                if src and not src.startswith("data:") and src not in image_urls:
                    image_urls.append(src)
        
        if image_urls:
            bar_info["source_photoUrls"] = image_urls
            print(f"Found {len(bar_info['source_photoUrls'])} image URLs")
    
    except Exception as e:
        print(f"Error extracting bar info: {e}")
    
    return bar_info

async def navigate_to_next_bar(page: Page) -> bool:
    """
    Navigate to the next bar by clicking the right arrow button.
    
    Args:
        page: Playwright page object
        
    Returns:
        True if navigation was successful, False otherwise
    """
    try:
        # Find the right arrow button
        next_button = await page.query_selector("button:has(svg[data-icon='angle-right'])")
        
        if next_button:
            # Check if button is disabled
            is_disabled = await next_button.get_attribute("class")
            if is_disabled and "Button__disabled" in is_disabled:
                print("Reached the last bar, no more bars to navigate to")
                return False
            
            # Click the button to navigate to the next bar
            await next_button.click()
            
            # Wait for the page to update with longer timeouts
            await page.wait_for_load_state("networkidle", timeout=30000)
            await asyncio.sleep(5)  # Additional wait to ensure content loads completely
            
            print("Navigated to the next bar")
            return True
        else:
            print("Could not find the next button")
            return False
    
    except Exception as e:
        print(f"Error navigating to next bar: {e}")
        return False

async def scrape_wanderlog_bars_detailed() -> List[Dict[str, Any]]:
    """
    Main function to scrape Wanderlog bars by navigating through the detailed view of each bar.
    
    Returns:
        List of dictionaries containing bar information
    """
    print(f"Starting Wanderlog bar scraper (detailed view approach)...")
    
    bars = []
    
    async with async_playwright() as p:
        # Launch a browser
        browser = await p.chromium.launch(headless=False)  # Use headless=False to see what's happening
        context = await browser.new_context(
            user_agent=HEADERS['User-Agent'],
            viewport={'width': 1920, 'height': 1080}
        )
        
        # Open a new page
        page = await context.new_page()
        
        # Navigate to the URL
        print(f"Navigating to {URL}...")
        await page.goto(URL, wait_until='networkidle', timeout=60000)
        
        # Wait for the page to load fully
        await asyncio.sleep(10)
        
        # Take a screenshot for reference
        await page.screenshot(path="wanderlog_initial.png")
        
        # Wait for the first bar to be displayed
        print("Waiting for bar cards to load...")
        try:
            await page.wait_for_selector("div.PlaceCard__maxHeight", timeout=30000)
            print("Bar cards loaded")
        except Exception as e:
            print(f"Error waiting for bar cards: {e}")
            await browser.close()
            return []
        
        # Process each bar
        bar_count = 0
        max_bars = 50  # Maximum number of bars to process
        
        while bar_count < max_bars:
            print(f"\nProcessing bar {bar_count + 1}/{max_bars}")
            
            # Extract information from the current bar
            bar_info = await extract_bar_info(page)
            
            # Only add the bar if we found a name
            if bar_info["source_name"]:
                bars.append(bar_info)
                print(f"Added bar: {bar_info['source_name']}")
            else:
                print("Skipping bar due to missing name")
            
            # Navigate to the next bar
            if not await navigate_to_next_bar(page):
                print("No more bars to process")
                break
            
            # Give extra time for the new bar to load completely
            await asyncio.sleep(5)
            
            bar_count += 1
        
        # Take a final screenshot
        await page.screenshot(path="wanderlog_final.png")
        
        # Close the browser
        await browser.close()
    
    print(f"Extracted information for {len(bars)} bars")
    return bars

async def main():
    """
    Main entry point for the script.
    """
    # Scrape the bars
    bars = await scrape_wanderlog_bars_detailed()
    
    # Save the results to a JSON file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(bars, f, indent=2, ensure_ascii=False)
    
    print(f"Saved results to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())

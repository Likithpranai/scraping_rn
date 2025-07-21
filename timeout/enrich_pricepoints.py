import json
import requests
import time
import os
import sys
import re
from typing import Dict, List, Any, Optional

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def load_bars_data(file_path: str) -> List[Dict[str, Any]]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        sys.exit(1)

def save_bars_data(bars_data: List[Dict[str, Any]], file_path: str) -> None:
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(bars_data, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved updated data to {file_path}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        sys.exit(1)

def query_perplexity_for_pricepoint(driver, bar_name: str, bar_address: str) -> Optional[str]:
    """
    Query Perplexity for price point information using Selenium automation.
    
    Args:
        driver: Selenium WebDriver instance
        bar_name: Name of the bar
        bar_address: Address of the bar
        
    Returns:
        Price point information as a string (e.g., "$", "$$", "$$$", "$$$$") or None if not found
    """
    print(f"Querying Perplexity for price point of: {bar_name} at {bar_address}")
    query = f"What is the price range ($ to $$$$) of {bar_name} bar located at {bar_address} in Hong Kong? Please respond with just the dollar signs, like $, $$, $$$, or $$$$."
    
    print(f"Query: {query}")
    
    try:
        # Check if we need to navigate to Perplexity or if we're already there
        if "perplexity.ai" not in driver.current_url:
            driver.get("https://www.perplexity.ai")
            time.sleep(3)  # Wait for page to load
        
        # Find the search input field and clear any existing text
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[placeholder='Ask anything...']")),
            "Could not find search box"
        )
        search_box.clear()
        
        # Type the query and submit
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        
        print("Waiting for Perplexity response...")
        
        # Wait for the response to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-message-author='assistant']"))
        )
        
        # Give it a bit more time to fully render the response
        time.sleep(5)
        
        # Extract the response text
        response_element = driver.find_element(By.CSS_SELECTOR, "div[data-message-author='assistant']")
        response_text = response_element.text
        
        print(f"Raw response: {response_text[:200]}...")
        
        # Look for price indicators like $, $$, $$$, $$$$ in the response
        price_pattern = r'\${1,4}'  # Match $ to $$$$
        price_matches = re.findall(price_pattern, response_text)
        
        if price_matches:
            # Get the most common price indicator
            price_counts = {}
            for price in price_matches:
                if len(price) <= 4:  # Only consider valid price indicators ($ to $$$$)
                    price_counts[price] = price_counts.get(price, 0) + 1
            
            if price_counts:
                most_common_price = max(price_counts.items(), key=lambda x: x[1])[0]
                print(f"Found price point: {most_common_price}")
                return most_common_price
        
        print("Could not find price point in response")
        return None
        
    except TimeoutException:
        print("Timed out waiting for Perplexity response")
        return None
    except Exception as e:
        print(f"Error querying Perplexity: {e}")
        return None

def enrich_bars_with_pricepoints(bars_data: List[Dict[str, Any]], output_file: str) -> List[Dict[str, Any]]:
    total_bars = len(bars_data)
    
    # Initialize the WebDriver
    print("Initializing Chrome WebDriver...")
    options = webdriver.ChromeOptions()
    # Uncomment the line below if you want to run headless (no visible browser)
    # options.add_argument("--headless")
    
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.maximize_window()
        
        try:
            # Process each bar
            for i, bar in enumerate(bars_data):
                name = bar.get("name", "")
                address = bar.get("source_address", "")
                
                # Skip if we already have a price point or if name/address is missing
                if bar.get("source_pricepoint") or not name or not address:
                    print(f"Skipping {name}: Already has price point or missing information")
                    continue
                
                print(f"\nProcessing bar {i+1}/{total_bars}: {name}")
                
                # Query Perplexity for price point
                price_point = query_perplexity_for_pricepoint(driver, name, address)
                
                if price_point:
                    bar["source_pricepoint"] = price_point
                    print(f"Updated price point for {name}: {price_point}")
                    
                    # Save after each update to preserve progress
                    save_bars_data(bars_data, output_file)
                
                # Be nice to the service - wait between queries
                time.sleep(5)
                
        finally:
            # Always close the driver
            driver.quit()
            print("WebDriver closed")
            
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        sys.exit(1)
    
    return bars_data

def main():
    # Input and output file paths - use current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "timeout_bars.json")
    output_file = os.path.join(current_dir, "timeout_bars_enriched.json")
    
    print(f"Loading bar data from {input_file}...")
    bars_data = load_bars_data(input_file)
    print(f"Loaded {len(bars_data)} bars.")
    
    print("\nIMPORTANT NOTE:")
    print("This script will use Selenium to automate querying Perplexity.ai for price points.")
    print("A Chrome browser window will open and automatically search for each bar's price point.")
    print("The script will:")
    print("1. Open Perplexity.ai in Chrome")
    print("2. Search for price information for each bar")
    print("3. Extract price points from the responses")
    print("4. Update the JSON file with the results\n")
    
    user_input = input("Do you want to continue with the Selenium automation? (y/n): ")
    
    if user_input.lower() != 'y':
        print("Exiting without making changes.")
        return
    
    print("\nEnriching bars with price points...")
    updated_bars_data = enrich_bars_with_pricepoints(bars_data, output_file)
    
    print(f"\nSaving final enriched data to {output_file}...")
    save_bars_data(updated_bars_data, output_file)
    
    print("\nProcess complete!")
    print("The bars data has been enriched with price points from Perplexity.ai")

if __name__ == "__main__":
    main()

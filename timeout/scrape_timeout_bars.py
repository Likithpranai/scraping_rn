import requests
from bs4 import BeautifulSoup
import json
import re
import os

def scrape_timeout_bars():
    """
    Scrapes bar information from Timeout Hong Kong's best bars page and saves it as JSON.
    
    Extracts:
    - source_url
    - source_name
    - source_address
    - source_neighbourhood
    - source_pricepoint
    - source_photoUrls
    - source_categories
    """
    # URL of the page to scrape
    main_url = "https://www.timeout.com/hong-kong/bars-and-pubs/best-bars-hong-kong"
    base_url = "https://www.timeout.com"
    
    # Send request to the URL
    print(f"Fetching data from {main_url}...")
    response = requests.get(main_url)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        return
    
    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the section with the bars list
    bars_section = soup.find("h2", {"data-testid": "zone-title_testID"})
    
    # If we found the section heading, look for all articles after it
    bar_tiles = []
    if bars_section:
        # Find the parent container that holds all the bars
        parent_section = bars_section.find_parent("section")
        if parent_section:
            # Find all articles (bar tiles) within this section
            bar_tiles = parent_section.find_all("article")
    
    if not bar_tiles:
        print("No bar tiles found. The page structure might have changed.")
        return
    
    print(f"Found {len(bar_tiles)} bars. Processing...")
    
    # List to store bar data
    bars_data = []
    
    # Process each bar tile
    for i, tile in enumerate(bar_tiles, 1):
        print(f"Processing bar {i}/{len(bar_tiles)}...")
        
        # Initialize bar data dictionary
        bar_data = {
            "source_url": main_url,
            "source_name": "",  # Will be populated with the bar name
            "source_address": "",
            "source_neighbourhood": "",
            "source_pricepoint": "",
            "source_photoUrls": [],
            "source_categories": ["Bar"]
        }
        
        # Extract bar name
        name_element = tile.find("h3", {"data-testid": "tile-title_testID"})
        if name_element:
            # Remove the number and clean up the name
            name_text = name_element.text
            name_text = re.sub(r'^\d+\.', '', name_text).strip()
            bar_data["name"] = name_text
            bar_data["source_name"] = name_text  # Set source_name to the bar name
            print(f"Found bar: {name_text}")
        
        # Extract photo URL
        img_element = tile.find("img", {"data-testid": "responsive-image_testID"})
        if img_element and img_element.get("src"):
            bar_data["source_photoUrls"].append(img_element["src"])
        
        # Extract link to detailed page
        link_element = tile.find("a", href=True)
        if link_element:
            detail_url = link_element["href"]
            if not detail_url.startswith("http"):
                detail_url = base_url + detail_url
            
            # Scrape detailed page for more information
            try:
                detail_response = requests.get(detail_url)
                if detail_response.status_code == 200:
                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                    
                    # Extract address
                    address_section = detail_soup.find("div", class_=lambda c: c and "_details_" in c)
                    if address_section:
                        address_term = address_section.find("dt", text="Address")
                        if address_term:
                            address_descriptions = address_term.find_next_siblings("dd")
                            address_parts = [dd.text.strip() for dd in address_descriptions]
                            bar_data["source_address"] = ", ".join(address_parts)
                    
                    # Extract neighborhood
                    neighborhood_tags = detail_soup.find_all("li", class_=lambda c: c and "_tag_" in c)
                    for tag in neighborhood_tags:
                        tag_text = tag.get_text().strip()
                        # Assuming neighborhoods are typically single words or short phrases
                        if len(tag_text.split()) <= 3 and not any(char.isdigit() for char in tag_text):
                            bar_data["source_neighbourhood"] = tag_text
                            break
                    
                    # Extract additional photos
                    detail_imgs = detail_soup.find_all("img", class_=lambda c: c and "_image_" in c)
                    for img in detail_imgs:
                        if img.get("src") and img["src"] not in bar_data["source_photoUrls"]:
                            bar_data["source_photoUrls"].append(img["src"])
                    
                    # Extract price point (this is more speculative, looking for $ symbols)
                    price_indicators = detail_soup.find_all(string=re.compile(r'[\$£€¥]{1,4}'))
                    for indicator in price_indicators:
                        # Look for price patterns like $$$, ££, etc.
                        price_match = re.search(r'[\$£€¥]{1,4}', indicator)
                        if price_match:
                            bar_data["source_pricepoint"] = price_match.group()
                            break
            
            except Exception as e:
                print(f"Error scraping detail page for {bar_data.get('name', 'unknown bar')}: {e}")
        
        # Add to the list if we have at least a name
        if "name" in bar_data:
            bars_data.append(bar_data)
    
    # Save the data to a JSON file
    output_file = "timeout_bars.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(bars_data, f, indent=4, ensure_ascii=False)
    
    print(f"Successfully scraped {len(bars_data)} bars. Data saved to {output_file}")

if __name__ == "__main__":
    scrape_timeout_bars()

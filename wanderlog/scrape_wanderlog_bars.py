import requests
import json
import re
import time
from bs4 import BeautifulSoup
import os

def scrape_wanderlog_bars(url):
    """
    Scrape bar data from Wanderlog Hong Kong bars and drinks page
    """
    print(f"🔍 Scraping data from: {url}")
    
    try:
        # Send request to the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch the page. Status code: {response.status_code}")
            return []
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all bar entries - they are in div elements with specific class
        bar_entries = soup.find_all('div', class_='cursor-pointer clearfix BoardPlaceView__selected PlaceView__selectable PlaceView__selected')
        
        print(f"📊 Found {len(bar_entries)} bar entries")
        
        bars_data = []
        
        # Process each bar entry
        for index, bar_div in enumerate(bar_entries, 1):
            try:
                # Extract bar name and URL
                name_element = bar_div.find('a', class_='color-gray-900')
                if name_element:
                    name = name_element.text.strip()
                    url = f"https://wanderlog.com{name_element.get('href')}" if name_element.get('href').startswith('/') else name_element.get('href')
                else:
                    name = "Unknown"
                    url = ""
                
                # Extract ranking number
                ranking = index  # Default to the index if not found
                marker_label = bar_div.find('span', class_='MarkerIconWithColor__label')
                if marker_label:
                    try:
                        ranking = int(marker_label.text.strip())
                    except:
                        pass
                
                # Extract rating
                rating_element = bar_div.find('span', class_='font-weight-bold RatingWithLogo__yellowRating')
                rating = rating_element.text.strip() if rating_element else "N/A"
                
                # Extract number of reviews
                reviews_text = ""
                reviews_element = bar_div.find('span', class_='ml-1 text-muted')
                if reviews_element:
                    reviews_match = re.search(r'\((\d+)\)', reviews_element.text)
                    if reviews_match:
                        reviews_text = reviews_match.group(1)
                
                # Extract price level
                price_level = ""
                price_element = bar_div.find('span', class_='text-muted')
                if price_element:
                    price_level = price_element.text.strip()
                
                # Extract category/type
                category = ""
                category_element = bar_div.find('div', class_='badge Badge__lightGray text-nowrap Badge__shape-pill d-inline-flex align-items-center')
                if category_element:
                    category = category_element.text.strip()
                
                # Extract description
                description = ""
                desc_element = bar_div.find('div', class_='mt-2', string=lambda text: text and not text.startswith('Mentioned on'))
                if desc_element:
                    description = desc_element.text.strip()
                
                # Extract images
                images = []
                img_elements = bar_div.find_all('img', class_='w-100 h-100 object-fit-cover')
                for img in img_elements:
                    src = img.get('src')
                    if src and not src.endswith('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mO89+jZfwAI8wOnPlNO+wAAAABJRU5ErkJggg=='):
                        images.append(src)
                
                # Extract reviews/snippets
                reviews = []
                review_elements = bar_div.find_all('div', class_='PlaceSnippet')
                for review_elem in review_elements:
                    review_text_elem = review_elem.find('div', class_='ExpandableText__textClosed PlaceSnippet__text font-italic')
                    review_source_elem = review_elem.find('a', class_='font-italic PlaceSnippet__source')
                    
                    if review_text_elem:
                        review_text = review_text_elem.text.strip()
                        review_source = review_source_elem.text.strip() if review_source_elem else "Unknown"
                        reviews.append({
                            "text": review_text,
                            "source": review_source
                        })
                
                # Create bar data dictionary
                bar_data = {
                    "ranking": ranking,
                    "name": name,
                    "url": url,
                    "rating": rating,
                    "reviews_count": reviews_text,
                    "price_level": price_level,
                    "category": category,
                    "description": description,
                    "images": images,
                    "reviews": reviews
                }
                
                bars_data.append(bar_data)
                print(f"✓ Processed bar #{ranking}: {name}")
                
            except Exception as e:
                print(f"❌ Error processing bar #{index}: {str(e)}")
        
        return bars_data
        
    except Exception as e:
        print(f"❌ Error scraping the page: {str(e)}")
        return []

def save_to_json(data, filename):
    """Save data to a JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Data saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving data to file: {str(e)}")
        return False

def main():
    # URL to scrape
    url = "https://wanderlog.com/list/geoCategory/685/best-bars-and-drinks-in-hong-kong"
    
    # Create output directory if it doesn't exist
    os.makedirs('wanderlog', exist_ok=True)
    
    # Scrape the data
    bars_data = scrape_wanderlog_bars(url)
    
    if bars_data:
        # Prepare output data
        output_data = {
            "source_url": url,
            "total_bars": len(bars_data),
            "scraped_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "bars": bars_data
        }
        
        # Save to JSON file
        output_file = os.path.join('wanderlog', 'hong_kong_bars.json')
        save_to_json(output_data, output_file)
        
        print(f"\n✅ Scraping completed!")
        print(f"📊 Total bars scraped: {len(bars_data)}")
    else:
        print("❌ No data was scraped")

if __name__ == "__main__":
    main()

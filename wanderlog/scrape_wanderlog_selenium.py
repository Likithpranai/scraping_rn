import json
import time
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def setup_driver():
    """Set up and return a Selenium WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_wanderlog_bars(url):
    """
    Scrape bar data from Wanderlog Hong Kong bars and drinks page using Selenium
    """
    print(f"🔍 Scraping data from: {url}")
    
    driver = setup_driver()
    
    try:
        # Load the page
        driver.get(url)
        print("⏳ Page loaded, waiting for content to render...")
        
        # Wait for the bar entries to load
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "BoardPlaceView__selected")))
        
        # Scroll down to load all content
        print("⏳ Scrolling to load all content...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Wait for content to load
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        # Get the page source after JavaScript execution
        page_source = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all bar entries
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
                desc_elements = bar_div.find_all('div', class_='mt-2')
                for elem in desc_elements:
                    if elem.text and not elem.text.startswith('Mentioned on') and not elem.find('div', class_='badge'):
                        description = elem.text.strip()
                        break
                
                # Extract images
                images = []
                img_elements = bar_div.find_all('img', class_='w-100 h-100 object-fit-cover')
                for img in img_elements:
                    src = img.get('src')
                    srcset = img.get('srcset')
                    
                    # Skip placeholder images
                    if src and 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mO89+jZfwAI8wOnPlNO+wAAAABJRU5ErkJggg==' not in src:
                        if srcset:
                            # Get the highest resolution image from srcset
                            srcset_parts = srcset.split(',')
                            if srcset_parts:
                                highest_res = srcset_parts[-1].strip().split(' ')[0]
                                images.append(highest_res)
                        else:
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
                
                # Extract address if available
                address = ""
                address_element = bar_div.find('div', class_='text-muted')
                if address_element:
                    address = address_element.text.strip()
                
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
                    "address": address,
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
    
    finally:
        # Always close the driver
        driver.quit()

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

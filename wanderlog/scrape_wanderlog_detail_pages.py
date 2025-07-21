import json
import time
import os
import re
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def scrape_bar_details(page, bar_url, bar_name, ranking):
    """
    Scrape detailed information from a bar's individual page
    """
    print(f"🔍 Navigating to bar page: {bar_name} ({bar_url})")
    
    try:
        # Navigate to the bar's detail page
        await page.goto(bar_url, wait_until="networkidle", timeout=60000)
        print(f"✅ Loaded page for: {bar_name}")
        
        # Wait for content to load
        await page.wait_for_timeout(3000)
        
        # Get the page content
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract detailed information
        
        # Description - look for the main description text
        description = ""
        desc_elements = soup.find_all('div', class_='ExpandableText__textClosed')
        if desc_elements:
            description = desc_elements[0].text.strip()
        
        # Address
        address = ""
        address_elements = soup.find_all('div', class_='text-muted')
        for elem in address_elements:
            if elem.find('svg') and 'location' in str(elem.find('svg')):
                address = elem.text.strip()
                break
        
        # Rating
        rating = ""
        rating_element = soup.find('span', class_='font-weight-bold RatingWithLogo__yellowRating')
        if rating_element:
            rating = rating_element.text.strip()
        
        # Number of reviews
        reviews_count = ""
        reviews_element = soup.find('span', class_='ml-1 text-muted')
        if reviews_element:
            reviews_match = re.search(r'\((\d+)\)', reviews_element.text)
            if reviews_match:
                reviews_count = reviews_match.group(1)
        
        # Price level
        price_level = ""
        price_elements = soup.find_all('span', class_='text-muted')
        for elem in price_elements:
            if '$' in elem.text:
                price_level = elem.text.strip()
                break
        
        # Category/type
        category = ""
        category_elements = soup.find_all('div', class_='badge Badge__lightGray text-nowrap Badge__shape-pill d-inline-flex align-items-center')
        if category_elements:
            category = category_elements[0].text.strip()
        
        # Images
        images = []
        img_elements = soup.find_all('img', class_='w-100 h-100 object-fit-cover')
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
        
        # Reviews/snippets
        reviews = []
        review_elements = soup.find_all('div', class_='PlaceSnippet')
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
        
        # Opening hours
        opening_hours = ""
        hours_elements = soup.find_all('div', class_='text-muted')
        for elem in hours_elements:
            if elem.find('svg') and 'clock' in str(elem.find('svg')):
                opening_hours = elem.text.strip()
                break
        
        # Website
        website = ""
        website_elements = soup.find_all('a', target='_blank')
        for elem in website_elements:
            if elem.find('svg') and 'globe' in str(elem.find('svg')):
                website = elem.get('href')
                break
        
        # Phone number
        phone = ""
        phone_elements = soup.find_all('a')
        for elem in phone_elements:
            if elem.find('svg') and 'phone' in str(elem.find('svg')):
                phone = elem.text.strip()
                break
        
        # Create bar data dictionary
        bar_data = {
            "ranking": ranking,
            "name": bar_name,
            "url": bar_url,
            "description": description,
            "address": address,
            "rating": rating,
            "reviews_count": reviews_count,
            "price_level": price_level,
            "category": category,
            "opening_hours": opening_hours,
            "website": website,
            "phone": phone,
            "images": images,
            "reviews": reviews
        }
        
        print(f"✓ Successfully scraped details for: {bar_name}")
        return bar_data
        
    except Exception as e:
        print(f"❌ Error scraping bar details for {bar_name}: {str(e)}")
        return {
            "ranking": ranking,
            "name": bar_name,
            "url": bar_url,
            "error": str(e)
        }

async def scrape_wanderlog_bars(url):
    """
    Scrape bar data from Wanderlog Hong Kong bars and drinks page using Playwright
    """
    print(f"🔍 Scraping data from: {url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            # Navigate to the URL
            await page.goto(url, wait_until="networkidle", timeout=60000)
            print("⏳ Page loaded, waiting for content to render...")
            
            # Wait for some time to ensure JavaScript execution
            await page.wait_for_timeout(5000)
            
            # Scroll down to load all content
            print("⏳ Scrolling to load all content...")
            for _ in range(5):  # Scroll multiple times to ensure all content loads
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)  # Wait between scrolls
            
            # Get the page content
            content = await page.content()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all bar entries based on the structure provided by the user
            bar_entries = soup.find_all('div', class_='d-flex mb-2 align-items-center')
            
            print(f"📊 Found {len(bar_entries)} bar entries")
            
            bars_data = []
            
            # Process each bar entry
            for index, bar_div in enumerate(bar_entries, 1):
                try:
                    # Extract bar name and URL
                    name_element = bar_div.find('a', class_='color-gray-900')
                    if name_element:
                        bar_name = name_element.text.strip()
                        href = name_element.get('href')
                        bar_url = f"https://wanderlog.com{href}" if href.startswith('/') else href
                        
                        # Extract ranking number
                        ranking = index  # Default to the index if not found
                        marker_label = bar_div.find('span', class_='MarkerIconWithColor__label')
                        if marker_label:
                            try:
                                ranking = int(marker_label.text.strip())
                            except:
                                pass
                        
                        # Navigate to the bar's detail page and scrape details
                        bar_data = await scrape_bar_details(page, bar_url, bar_name, ranking)
                        bars_data.append(bar_data)
                    
                except Exception as e:
                    print(f"❌ Error processing bar #{index}: {str(e)}")
            
            return bars_data
            
        except Exception as e:
            print(f"❌ Error scraping the page: {str(e)}")
            return []
        
        finally:
            # Always close the browser
            await browser.close()

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

async def main():
    # URL to scrape
    url = "https://wanderlog.com/list/geoCategory/685/best-bars-and-drinks-in-hong-kong"
    
    # Create output directory if it doesn't exist
    os.makedirs('wanderlog', exist_ok=True)
    
    # Scrape the data
    bars_data = await scrape_wanderlog_bars(url)
    
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
    asyncio.run(main())

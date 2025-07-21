import json
import time
import os
import re
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def scrape_bar_details(page, bar_url, bar_name, ranking):
    """
    Scrape detailed information from a bar's individual page using the exact selectors provided
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
        
        # Extract detailed information using the exact selectors provided
        
        # 1. source_url - URL of the current page
        source_url = bar_url
        
        # 2. source_name - from h1 tag
        source_name = bar_name  # Default to the name we already have
        name_element = soup.find('h1', class_='font-weight-bold mb-3 line-height-1 color-primary-darkest')
        if name_element:
            source_name = name_element.text.strip()
        
        # 3. source_address - from Google Maps link
        source_address = ""
        address_links = soup.find_all('a', href=lambda href: href and 'google.com/maps/search' in href)
        if address_links:
            source_address = address_links[0].text.strip()
        
        # 4. source_neighbourhood - will be extracted from address later
        # (This will be processed outside the scraping function)
        
        # 5. source_pricepoint - look for $ symbols
        source_pricepoint = ""
        price_elements = soup.find_all('span', class_='text-muted')
        for elem in price_elements:
            if '$' in elem.text:
                source_pricepoint = elem.text.strip()
                break
        
        # 6. source_photoUrls - get all image URLs with the specified class
        source_photoUrls = []
        img_elements = soup.find_all('img', class_='w-100 h-100 object-fit-cover')
        for img in img_elements:
            src = img.get('src')
            srcset = img.get('srcset')
            
            # Skip placeholder images
            if src and 'data:image/png;base64,' not in src:
                if srcset:
                    # Get the highest resolution image from srcset
                    srcset_parts = srcset.split(',')
                    if srcset_parts:
                        highest_res = srcset_parts[-1].strip().split(' ')[0]
                        source_photoUrls.append(highest_res)
                else:
                    source_photoUrls.append(src)
        
        # 7. source_categories - get all badge content
        source_categories = []
        category_container = soup.find('div', class_='d-flex flex-row align-items-center mt-2 flex-wrap')
        if category_container:
            badges = category_container.find_all('div', class_='badge Badge__lightGray text-nowrap Badge__shape-pill d-inline-flex align-items-center')
            for badge in badges:
                category = badge.text.strip()
                if category and category != "Closed":
                    source_categories.append(category)
        
        # Additional information that might be useful
        
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
        
        # Description
        description = ""
        desc_elements = soup.find_all('div', class_='ExpandableText__textClosed')
        if desc_elements:
            description = desc_elements[0].text.strip()
        
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
        
        # Create bar data dictionary with the required fields
        bar_data = {
            "ranking": ranking,
            "source_url": source_url,
            "source_name": source_name,
            "source_address": source_address,
            "source_neighbourhood": "",  # Will be processed later
            "source_pricepoint": source_pricepoint,
            "source_photoUrls": source_photoUrls,
            "source_categories": source_categories,
            "rating": rating,
            "reviews_count": reviews_count,
            "description": description,
            "reviews": reviews
        }
        
        print(f"✓ Successfully scraped details for: {source_name}")
        return bar_data
        
    except Exception as e:
        print(f"❌ Error scraping bar details for {bar_name}: {str(e)}")
        return {
            "ranking": ranking,
            "source_url": bar_url,
            "source_name": bar_name,
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

def extract_neighbourhood(address):
    """
    Extract neighbourhood from address (simplified version)
    In a real implementation, this would use a more sophisticated approach or API
    """
    if not address:
        return ""
    
    # Simple extraction based on common Hong Kong districts
    districts = [
        "Central", "Wan Chai", "Causeway Bay", "Tsim Sha Tsui", "Mong Kok", 
        "Sheung Wan", "Kennedy Town", "Sai Ying Pun", "Admiralty", "North Point",
        "Quarry Bay", "Tai Koo", "Chai Wan", "Shau Kei Wan", "Yau Ma Tei",
        "Jordan", "Hung Hom", "Kwun Tong", "Sham Shui Po", "Lai Chi Kok"
    ]
    
    for district in districts:
        if district in address:
            return district
    
    return ""

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
        # Post-process the data to extract neighbourhoods
        for bar in bars_data:
            if "source_address" in bar:
                bar["source_neighbourhood"] = extract_neighbourhood(bar["source_address"])
        
        # Prepare output data
        output_data = {
            "source_url": url,
            "total_bars": len(bars_data),
            "scraped_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "bars": bars_data
        }
        
        # Save to JSON file
        output_file = os.path.join('wanderlog', 'hong_kong_bars_final.json')
        save_to_json(output_data, output_file)
        
        print(f"\n✅ Scraping completed!")
        print(f"📊 Total bars scraped: {len(bars_data)}")
    else:
        print("❌ No data was scraped")

if __name__ == "__main__":
    asyncio.run(main())

import requests
import json
import re
import time

def extract_urls_from_file(file_path):
    """Extract all URLs from the eventbrite_links file."""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Find all URLs in the comments (lines starting with #)
            url_pattern = r'(https?://[^\s]+)'
            urls = re.findall(url_pattern, content)
        return urls
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def scrape_links_from_url(url, api_key):
    """Scrape links from a single URL using ScrapingBee API."""
    try:
        response = requests.get(
            url='https://app.scrapingbee.com/api/v1',
            params={
                'api_key': api_key,
                'url': url,
                'wait': '10000',
                'extract_rules': '{"all_links":{"selector":"a@href","type":"list"}}'
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            links = data.get('all_links', [])
            # Filter out None values and javascript links
            filtered_links = [link for link in links if link and not link.startswith('javascript:')]
            print(f"✓ Scraped {len(filtered_links)} links from: {url}")
            return filtered_links
        else:
            print(f"✗ HTTP {response.status_code} for: {url}")
            return []
    except Exception as e:
        print(f"✗ Error scraping {url}: {e}")
        return []

def main():
    # Your ScrapingBee API key
    API_KEY = 'YGD6CRSSN2H9MT70H6VWQXHKL0UW6QEKATV7LJ2HPERIH2DJ0W4EKU5XYFZISG01BZ3RNDXSP5CSARAS'
    
    # Extract URLs from the file
    print("📄 Extracting URLs from eventbrite_links...")
    urls = extract_urls_from_file('eventbrite_links')
    
    if not urls:
        print("❌ No URLs found in the file")
        return
    
    print(f"🔍 Found {len(urls)} URLs to scrape")
    
    # Scrape all URLsx
    all_links = []
    for i, url in enumerate(urls, 1):
        print(f"\n🔄 Scraping URL {i}/{len(urls)}")
        links = scrape_links_from_url(url, API_KEY)
        all_links.extend(links)
        
        # Add a small delay between requests
        time.sleep(1)
    
    # Remove duplicates while preserving order
    unique_links = []
    seen = set()
    for link in all_links:
        if link not in seen:
            unique_links.append(link)
            seen.add(link)
    
    # Prepare final output
    output_data = {
        'total_urls_scraped': len(urls),
        'total_links_found': len(unique_links),
        'all_links': unique_links
    }
    
    # Save to JSON file
    with open('scraped_links_eventbrite5.json', 'w', encoding='utf-8') as file:
        json.dump(output_data, file, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Scraping completed!")
    print(f"📊 Total URLs scraped: {len(urls)}")
    print(f"📊 Total unique links found: {len(unique_links)}")
    print(f"💾 Results saved to: scraped_links_eventbrite5.json")

if __name__ == "__main__":
    main()

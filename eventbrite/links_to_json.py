import requests
import os
import json
import re
from bs4 import BeautifulSoup

API_KEY = 'e040fc494447cdd06abfa70304bf211f'
LINKS_FILE = 'eventbrite/unique_eventbrite_links.txt'
OUTPUT_FILE = 'eventbrite/scraped_eventbrite.json'

# Load finished links if any
finished = {}
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        try:
            finished_list = json.load(f)
            finished = {obj['url']: obj for obj in finished_list if 'url' in obj}
        except Exception:
            finished = {}

# Load all links
with open(LINKS_FILE, 'r', encoding='utf-8') as f:
    links = [line.strip() for line in f if line.strip()]

results = list(finished.values())

for link in links:
    if link in finished:
        continue
    payload = {'api_key': API_KEY, 'url': link}
    try:
        r = requests.get('https://api.scraperapi.com/', params=payload, timeout=30)
        html = r.text
        soup = BeautifulSoup(html, 'html.parser')
        result = {}
        # imagesUrls
        images = []
        img_hero = soup.find('img', {'data-testid': 'hero-img'})
        if img_hero and img_hero.get('src'):
            images.append(img_hero['src'])
        for img in soup.find_all('img', class_='eds-max-img'):
            if img.get('src'):
                images.append(img['src'])
        result['imagesUrls'] = images
        # title
        h1 = soup.find('h1', class_='event-title')
        title = h1.get_text(strip=True) if h1 else None
        title = re.sub(r'\s+', ' ', title).strip() if title else None
        result['title'] = title
        # summary
        summary = None
        p_summary = soup.find('p', class_='summary')
        if p_summary:
            strong = p_summary.find('strong')
            if strong:
                summary = strong.get_text(strip=True)
                summary = re.sub(r'\s+', ' ', summary).strip()
        result['summary'] = summary
        # organizer
        organizer = None
        strong_org = soup.find('strong', class_='organizer-listing-info-variant-b__name-link')
        if strong_org:
            organizer = strong_org.get_text(strip=True)
            organizer = re.sub(r'\s+', ' ', organizer).strip()
        result['organizer'] = organizer
        # datesAndTimes
        dates = []
        for time_tag in soup.select('div.DateCard-module__root___28_4K time'):
            if time_tag.has_attr('datetime'):
                dates.append(time_tag['datetime'])
        if not dates:
            for span in soup.select('span.date-info__full-datetime'):
                dates.append(span.get_text(strip=True))
        result['datesAndTimes'] = dates
        # venue (from JSON-LD)
        venue = None
        jsonld = None
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if 'location' in data and 'address' in data['location']:
                    jsonld = data
                    break
            except Exception:
                continue
        if jsonld:
            venue_name = jsonld['location'].get('name', '')
            address = jsonld['location']['address']
            venue_parts = [address.get('streetAddress', ''), address.get('addressLocality', ''), address.get('addressRegion', '')]
            venue = venue_name + ', ' + ', '.join([part for part in venue_parts if part])
        result['venue'] = venue
        # description (from JSON-LD or fallback)
        description = None
        desc_div = soup.find('div', class_='eds-text--left')
        if desc_div:
            paragraphs = desc_div.find_all('p')
            description = ' '.join([re.sub(r'\s+', ' ', p.get_text()).strip() for p in paragraphs if p.get_text(strip=True)])
        result['description'] = description
        # price (from JSON-LD)
        price = None
        if jsonld and 'offers' in jsonld:
            offers = jsonld['offers']
            if isinstance(offers, list):
                for offer in offers:
                    if 'price' in offer and 'priceCurrency' in offer:
                        price = f"{offer['price']} {offer['priceCurrency']}"
                        break
        result['price'] = price
        # url (from JSON-LD)
        url = None
        if jsonld and 'url' in jsonld:
            url = jsonld['url']
        result['url'] = url or link
        results.append(result)
        # Save progress after each link
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Scraped: {link}")
    except Exception as e:
        print(f"Error scraping {link}: {e}")
        continue
print(f"Done. {len(results)} events scraped.")

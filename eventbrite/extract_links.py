import json
import os

DIR = os.path.dirname(__file__)
FILES = [
    'scraped_links_eventbrite.json',
    'scraped_links_eventbrite2.json',
    'scraped_links_eventbrite3.json',
    'scraped_links_eventbrite4.json',
    'scraped_links_eventbrite5.json',
]

PREFIXES = [
    'https://www.eventbrite.hk/e/',
    'https://www.eventbrite.com/e/'
]

SUFFIX = '?aff=ebdssbdestsearch'

unique_links = set()

for fname in FILES:
    path = os.path.join(DIR, fname)
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        links = data.get('all_links', [])
        for link in links:
            # Remove suffix if present
            if link.endswith(SUFFIX):
                link = link[:-len(SUFFIX)]
            if any(link.startswith(prefix) for prefix in PREFIXES):
                unique_links.add(link)

output_path = os.path.join(DIR, 'unique_eventbrite_links.txt')
with open(output_path, 'w', encoding='utf-8') as out:
    for link in sorted(unique_links):
        out.write(link + '\n')

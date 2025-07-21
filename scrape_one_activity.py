import requests

url = 'https://api.scraperapi.com/'
# Define headers with your API key and rendering settings
headers = {
    'x-sapi-api_key': 'f69e167a1d6e40586b86c50b79f6e4a0',
    'x-sapi-render': 'true',
    'x-sapi-retry_404': 'true',
    # 'x-sapi-instruction_set': '[{"type": "wait", "value": 10}]'
}
payload = {
    'url': 'https://www.klook.com/activity/83981-hongkong-skyline-cruise-victoria-harbour-tour/'
}
response = requests.get(url, params=payload, headers=headers)

# Get the HTML text
html_text = response.text

# Write the whole text to activity_test_all.txt
with open('activity_test_all.txt', 'w', encoding='utf-8') as f:
    f.write(html_text)

# Find the longest line in the HTML text
lines = html_text.split('\n')
longest_line = max(lines, key=len)

# Write the longest line to activity_test_1line.txt
with open('activity_test_1line.txt', 'w', encoding='utf-8') as f:
    f.write(longest_line)

print(f"Longest line length: {len(longest_line)}")
print(f"Total lines: {len(lines)}")
print("Files written: activity_test_all.txt and activity_test_1line.txt")
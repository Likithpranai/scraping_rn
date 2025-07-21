import requests

url = 'https://api.scraperapi.com/'
# Define headers with your API key and rendering settings
headers = {'x-sapi-api_key': 'f69e167a1d6e40586b86c50b79f6e4a0', 'x-sapi-render': 'true',
           'x-sapi-instruction_set': '[{"type": "wait_for_event","event": "networkidle","timeout": 30}]'}
payload = {
    'url': 'https://www.klook.com/activity/44068-thann-sanctuary-spa-experience-hong-kong/'
}
response = requests.get(url, params=payload, headers=headers)

if response.status_code == 200:
    html_content = response.text
    
    print(html_content)

    with open("result.html", "w", encoding="utf-8") as f:
        f.write(html_content)
else:
    print(f"Error: Request failed with status code {response.status_code}")
    print(response.text)

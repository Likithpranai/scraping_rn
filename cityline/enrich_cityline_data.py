import os
import json
import logging
import time
import requests

# --- Configuration ---
INPUT_FILE = 'cityline/cityline_data.json'
OUTPUT_FILE = 'cityline/enriched_cityline_data.json'
SAMPLE_FULL_OBJECT_FILE = os.path.join('', 'sample_full_object.json') # Navigate up to the parent directory
PERPLEXITY_API_KEY =  "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" # It's recommended to use environment variables for API keys

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions ---
def load_json_file(filename, is_list=False):
    """Loads a JSON file and returns its content."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"File not found: {filename}. Returning default value.")
        return [] if is_list else {}
    except json.JSONDecodeError:
        logging.error(f"Could not decode JSON from {filename}. Returning default value.")
        return [] if is_list else {}

def save_json_file(data, filename):
    """Saves data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def create_prompt(search_query, sample_full_object):
    """Creates the prompt for the Perplexity API to generate a full data object based on a search query."""
    prompt = f"""
**Instructions:**
1.  Search online for "{search_query}" and find the event details.
2.  Gather all information about this event you can find on the internet.
3.  Generate a single, complete JSON object for this activity.
4.  Strictly follow the structure, format, and data types of the "Example Full Object (Target Schema)".
5.  Adhere to the detailed field descriptions provided below.
6.  Do not include any explanations, apologies, or markdown formatting (like ```json) in your response. Output only the raw JSON object.

**Field Descriptions (Source Data):**
- `source_url`: (string) The direct URL to the activity's booking or information page.
- `source_name`: (string) The official name of the activity or package.
- `source_address`: (string) The full street address of the venue.
- `source_pricePoint`: (string) The starting price, formatted as a string with a currency symbol (e.g., "$1480", "Free").
- `source_rating`: (float) The public rating of the activity (e.g., 4.8). If not available, provide a reasonable estimate.
- `source_introduction`: (string) A detailed, factual paragraph describing the activity, its offerings, and what's included.
- `source_Categories`: (string) A comma-separated list of relevant categories (e.g., "Tours & experiences,Massages,Spa & massages").

**Field Descriptions (Enrichment Data):**
- `enrich_localName`: (string) The name of the event in Traditional Chinese. Keep company/brand names like "The Murray" or "Grand Hyatt" in English.
- `enrich_englishName`: (string) The name of the event in English.
- `enrich_type`: (string) Classify as either "local activities" or "events".
- `enrich_neighborhood`: (string) The specific district name from the address (e.g., "Central", "Tsim Sha Tsui", "Causeway Bay").
- `enrich_hiddenGemScore`: (integer) A score from 0-100. High score (80-100) for unique, local workshops. Low score (0-30) for major hotel spas or international brands.
- `enrich_textEmbedding`: (string) A comprehensive, paragraph-style summary combining title, summary, and highlights for vector embeddings.
- `enrich_tagsType`: (JSON object) Distribute 100 points across categories: {{"Food": 0, "Nature": 0, "Sports": 0, "Leisure": 0, "Shopping": 0, "Wellness": 0, "Adventure": 0, "Nightlife": 0, "Educational": 0, "Hidden Gems": 0, "Photography": 0, "Art & Culture": 0, "Entertainment": 0}}. Sum must be 100.
- `enrich_tagsBudget`: (JSON object) Set exactly one category to 1 and all others to 0: {{"Free": 0, "Budget friendly": 0, "Moderately priced": 0, "High-end": 0, "Luxury": 0}}. Base this on the `source_pricePoint`.
- `enrich_tagsGroup`: (JSON object) Distribute 100 points across group types: {{"Date": 0, "Kids": 0, "Family": 0, "Friends": 0, "Business": 0, "Colleagues": 0}}. Sum must be 100.
- `enrich_description`: (string) A concise, appealing description of the activity, under 20 words.

**Example Full Object (Target Schema):**
```json
{json.dumps(sample_full_object, indent=2, ensure_ascii=False)}
```

**Search Query:**
"{search_query}"

**Your generated JSON object:**
"""
    return prompt

def call_perplexity_api(prompt):
    """Calls the Perplexity API and returns the response content."""
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant that provides structured JSON data."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        # Extract the content from the response
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        return content
    except requests.exceptions.RequestException as e:
        logging.error(f"API request failed: {e}")
        return None
    except (KeyError, IndexError) as e:
        logging.error(f"Failed to parse API response: {e}")
        return None


def process_item(item, sample_full_object):
    """Processes a single item, calls Perplexity API, and handles the response."""
    item_name = item.get('name')
    if not item_name:
        logging.warning("Skipping item with no name.")
        return None

    logging.info(f"Processing item: {item_name}")

    # Create search query from name and tags
    tags = item.get('tags', [])
    search_query = f"{item_name} {' '.join(tags)}"

    print(f"Search Query: {search_query}")
    
    prompt = create_prompt(search_query, sample_full_object)
    
    api_response = call_perplexity_api(prompt)
    
    if not api_response:
        logging.error(f"No response from API for item: {item_name}")
        return None

    try:
        # The API might return the JSON string within a markdown block
        clean_response = api_response.strip().replace('```json', '').replace('```', '').strip()
        enriched_data = json.loads(clean_response)
        
        # Merge the original name for tracking
        enriched_data['cityline_name'] = item_name
        
        return enriched_data
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON response for item: {item_name}")
        logging.debug(f"Problematic response:\n{api_response}")
        return None

# --- Main Execution ---
def main():
    """Main function to run the enrichment script."""
    if not PERPLEXITY_API_KEY:
        logging.error("PERPLEXITY_API_KEY environment variable not set. Please set it before running.")
        exit(1)

    # Load data
    cityline_data = load_json_file(INPUT_FILE, is_list=True)
    if not cityline_data:
        logging.info("No data found in cityline_data.json. Exiting.")
        return

    sample_full_object = load_json_file(SAMPLE_FULL_OBJECT_FILE)
    if not sample_full_object:
        logging.error(f"Could not load the sample object from {SAMPLE_FULL_OBJECT_FILE}. Exiting.")
        return

    # Load already processed data to allow for resuming
    enriched_results = load_json_file(OUTPUT_FILE, is_list=True)
    processed_names = {item.get('cityline_name') for item in enriched_results}
    
    logging.info(f"Found {len(processed_names)} already processed items.")

    # Process new items
    for item in cityline_data:
        item_name = item.get('name')
        if not item_name:
            logging.warning(f"Skipping item because it has no 'name' field: {item}")
            continue
            
        if item_name in processed_names:
            logging.info(f"Skipping already processed item: {item_name}")
            continue

        enriched_item = process_item(item, sample_full_object)
        if enriched_item:
            enriched_results.append(enriched_item)
            processed_names.add(item_name) # Add to set to avoid re-processing in the same run
            
            # Save after each successful processing to avoid data loss
            save_json_file(enriched_results, OUTPUT_FILE)
            logging.info(f"Successfully processed and saved item: {item_name}. Total saved: {len(enriched_results)}")
        else:
            logging.warning(f"Failed to process item: {item_name}")

        # Respectful delay to avoid overwhelming the API
        time.sleep(2)

    logging.info("Enrichment process completed.")

if __name__ == "__main__":
    main()

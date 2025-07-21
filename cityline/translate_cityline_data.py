import os
import json
import logging
import time
from cerebras.cloud.sdk import Cerebras
from langdetect import detect, LangDetectException

import re

def remove_think_block(text):
    # Remove <think>...</think> using regex (non-greedy match)
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return cleaned.strip()

# --- Configuration ---
INPUT_FILE = 'cityline/enriched_cityline_data.json'
OUTPUT_FILE = 'cityline/translated_cityline_data.json'
UNPARSABLE_DIR = 'cityline/unparsable_translations'
MODEL_NAME = "qwen-3-32b"  # Using a model from the reference script
# It's recommended to use environment variables for API keys
CEREBRAS_API_KEY = os.environ.get("CEREBRAS_API_KEY", "csk-krynjw3xc6kprx4dm4j288ktv5w3rck524m6ddvt2tvfyx4j")

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Initialize Cerebras Client ---
try:
    client = Cerebras(api_key=CEREBRAS_API_KEY)
except Exception as e:
    logging.error(f"Failed to initialize Cerebras client: {e}")
    exit(1)

# --- Helper Functions ---
def load_json_file(filename):
    """Loads a JSON file and returns its content."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"File not found: {filename}. Returning empty list.")
        return []
    except json.JSONDecodeError:
        logging.error(f"Could not decode JSON from {filename}. Returning empty list.")
        return []

def save_json_file(data, filename):
    """Saves data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def is_english(text):
    """Checks if the given text is in English."""
    if not text or not isinstance(text, str):
        return True  # Assume non-string or empty text doesn't need translation
    try:
        return detect(text) == 'en'
    except LangDetectException:
        # If language detection fails (e.g., text is too short or ambiguous),
        # assume it might need translation to be safe, or handle as needed.
        # For addresses/short text, it might be better to assume it's not English if detection fails.
        return False

def create_translation_prompt(item_data):
    """Creates a prompt to translate specific fields in a JSON object."""
    prompt = f"""
You are an expert translation AI. Your task is to translate specific fields within a JSON object to English.

**Instructions:**
1.  Analyze the provided "Original JSON Object".
2.  Identify the following fields: `source_address`, `enrich_neighborhood`, `enrich_textEmbedding`, `source_introduction`, `source_Categories` and `enrich_description`.
3.  Translate the values of these fields into natural, fluent English.
4.  If a field is already in English, keep its original value.
5.  Return the *entire*, complete JSON object with only the specified fields translated.
6.  Do not alter the structure, keys, or any other values in the JSON object.
7.  Do not include any explanations, apologies, or markdown formatting (like ```json) in your response. Output only the raw, updated JSON object.

**Original JSON Object:**
```json
{json.dumps(item_data, indent=2, ensure_ascii=False)}
```

**Your translated JSON object:**
"""
    return prompt

def process_item(item, processed_ids):
    """Processes a single item, translates if necessary, and returns the result."""
    item_id = item.get('cityline_name') or item.get('source_name')
    if not item_id:
        logging.warning("Skipping item with no 'cityline_name' or 'source_name'.")
        return None
    
    if item_id in processed_ids:
        logging.info(f"Skipping already processed item: {item_id}")
        return None

    logging.info(f"Processing item: {item_id}")

    # Check if translation is needed
    address = item.get('source_address', '')
    neighborhood = item.get('enrich_neighborhood', '')
    embedding_text = item.get('enrich_textEmbedding', '')
    introduction = item.get('source_introduction', '')
    categories = item.get('source_Categories', '')
    description = item.get('enrich_description', '')

    if is_english(address) and is_english(neighborhood) and is_english(embedding_text) and is_english(introduction) and is_english(categories) and is_english(description):
        logging.info(f"Item '{item_id}' is already in English. Skipping API call.")
        return item

    # If translation is needed, call the API
    prompt = create_translation_prompt(item)
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_NAME,
        )
        response_content = chat_completion.choices[0].message.content

        response_content = remove_think_block(response_content)

        # Clean up the response
        if response_content.strip().startswith("```json"):
            response_content = response_content.strip()[7:-3].strip()

        
        
        translated_data = json.loads(response_content)
        logging.info(f"Successfully translated and parsed data for item: {item_id}")
        return translated_data

    except json.JSONDecodeError:
        logging.error(f"Failed to parse JSON response for item: {item_id}. Saving to unparsable.")
        # Sanitize the item_id to create a valid filename
        filename = "".join(c for c in item_id if c.isalnum() or c in (' ', '_')).rstrip()
        with open(os.path.join(UNPARSABLE_DIR, f"unparsable_{filename}.txt"), 'w', encoding='utf-8') as f:
            f.write(response_content)
        return None
    except Exception as e:
        logging.error(f"An error occurred while processing {item_id}: {e}")
        return None

# --- Main Execution ---
def main():
    """Main function to run the translation script."""
    if not CEREBRAS_API_KEY:
        logging.error("CEREBRAS_API_KEY environment variable not set.")
        exit(1)

    # Load data
    source_data = load_json_file(INPUT_FILE)
    if not source_data:
        logging.info(f"No data found in {INPUT_FILE}. Exiting.")
        return

    # Load already processed data to allow for resuming
    translated_results = load_json_file(OUTPUT_FILE)
    processed_ids = {item.get('cityline_name') or item.get('source_name') for item in translated_results}
    
    logging.info(f"Found {len(processed_ids)} already processed items.")

    # Process new items
    for item in source_data:
        processed_item = process_item(item, processed_ids)
        
        if processed_item:
            translated_results.append(processed_item)
            item_id = processed_item.get('cityline_name') or processed_item.get('source_name')
            processed_ids.add(item_id)
            
            # Save after each successful processing
            save_json_file(translated_results, OUTPUT_FILE)
            logging.info(f"Processed and saved item: {item_id}. Total saved: {len(translated_results)}")
        
        time.sleep(1) # Add a small delay to be respectful to the API

    logging.info("Translation process completed.")

if __name__ == "__main__":
    if not os.path.exists(UNPARSABLE_DIR):
        os.makedirs(UNPARSABLE_DIR)
    main()

import os
import json
from cerebras.cloud.sdk import Cerebras
import logging
import re
import time

# --- Configuration ---
INPUT_FILE = 'transformed_klook_data.json'
SAMPLE_ENRICHED_FILE = 'sample_enriched_object.json'
OUTPUT_DIR = 'enrichment_output'
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'enriched_klook_data.json')
UNPARSABLE_DIR = os.path.join(OUTPUT_DIR, 'unparsable_enrichment_results')
MODELS = [
    "llama-4-scout-17b-16e-instruct",
    "llama3.3-70b",
    "qwen-3-235b-a22b",
    "qwen-3-32b"
]
current_model_index = 0

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Initialize Cerebras Client ---
try:
    # It's recommended to use environment variables for API keys
    api_key = "csk-3npmnd99fv6ye8xkvn9v9v88fk5mr3yf3354rk8rdynme38x"
    if not api_key:
        raise ValueError("Cerebras API key not found. Please set the CEREBRAS_API_KEY environment variable.")
    client = Cerebras(api_key=api_key)
except Exception as e:
    logging.error(f"Failed to initialize Cerebras client: {e}")
    exit(1)

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
        logging.error(f"Could not decode JSON from {filename}. Please check its format.")
        return [] if is_list else {}

def save_json_file(data, filename):
    """Saves data to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def create_prompt(item_data, sample_enriched_object):
    """Creates the prompt for the Cerebras API to enrich a single data object."""
    # Extract only the enrichment fields for the example
    sample_enrichment_only = {k: v for k, v in sample_enriched_object.items() if k.startswith('enrich_')}

    prompt = f"""
You are an expert data enrichment AI. Your task is to take a JSON object about a local activity and generate a new JSON object containing only enrichment fields.

**Instructions:**
1.  Analyze the provided "Input Activity Data".
2.  Generate a single JSON object that includes ONLY the new `enrich_` fields.
3.  Strictly follow the structure and format of the "Example Enrichment Object (Target Format)".
4.  Adhere to the descriptions for each `enrich_` field provided below.
5.  Do not include any explanations, apologies, or markdown formatting (like ```json) in your response. Output only the raw JSON object containing the enrichment fields.

**Field Descriptions for Enrichment:**
- `enrich_localName`: (string) The name of the event in Traditional Chinese. Keep company/brand names like "The Murray" or "Grand Hyatt" in English.
- `enrich_englishName`: (string) The name of the event in English.
- `enrich_type`: (string) Classify as either "local activities" or "events".
- `enrich_neighborhood`: (string) The specific district name from the address (e.g., "Central", "Tsim Sha Tsui", "Causeway Bay"). If not obvious, derive from context.
- `enrich_hiddenGemScore`: (integer) A score from 0-100. A high score (80-100) for very local, unique workshops. A low score (0-30) for major, well-known hotel spas or international brands.
- `enrich_textEmbedding`: (string) A comprehensive, paragraph-style summary of the activity, combining its title, summary, and highlights. This will be used for vector embeddings.
- `enrich_tagsType`: (JSON object) Distribute 100 points across categories: {{"Food": 0, "Nature": 0, "Sports": 0, "Leisure": 0, "Shopping": 0, "Wellness": 0, "Adventure": 0, "Nightlife": 0, "Educational": 0, "Hidden Gems": 0, "Photography": 0, "Art & Culture": 0, "Entertainment": 0}}. The sum of values must be 100.
- `enrich_tagsBudget`: (JSON object) Set exactly one category to 1 and all others to 0: {{"Free": 0, "Budget friendly": 0, "Moderately priced": 0, "High-end": 0, "Luxury": 0}}. Base this on the `source_pricePoint`.
- `enrich_tagsGroup`: (JSON object) Distribute 100 points across group types: {{"Date": 0, "Kids": 0, "Family": 0, "Friends": 0, "Business": 0, "Colleagues": 0}}. The sum of values must be 100.
- `enrich_description`: (string) A concise, appealing description of the activity, under 20 words.

**Example Enrichment Object (Target Format):**
```json
{json.dumps(sample_enrichment_only, indent=2, ensure_ascii=False)}
```

**Input Activity Data:**
```json
{json.dumps(item_data, indent=2, ensure_ascii=False)}
```

**Your generated JSON object (enrichment fields only):**
"""
    return prompt

def process_item(item, sample_enriched_object, processed_ids):
    """Processes a single item, calls Cerebras API, and handles the response."""
    global current_model_index
    item_id = item.get('klook_id')
    if not item_id:
        logging.warning(f"Skipping item without klook_id: {item.get('klook_title')}")
        return None
    
    if item_id in processed_ids:
        logging.info(f"Skipping already processed item ID: {item_id}")
        return None

    logging.info(f"Processing item: {item_id} - {item.get('klook_title')}")

    prompt = create_prompt(item, sample_enriched_object)

    # --- Model Rotation and Retry Logic ---
    initial_model_index = current_model_index
    while True:
        model_name = MODELS[current_model_index]
        logging.info(f"Attempting to use model: {model_name}")

        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model_name,
                temperature=0.1, # Lower temperature for more deterministic JSON output
            )
            response_content = chat_completion.choices[0].message.content

            # Clean up the response to extract only the JSON part
            json_string = response_content
            # Find the first '{' and the last '}' to extract the JSON block
            start_index = response_content.find('{')
            end_index = response_content.rfind('}')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                json_string = response_content[start_index:end_index+1]
            
            # Attempt to parse the JSON
            enrichment_data = json.loads(json_string)

            # Merge original item with new enrichment data
            combined_data = {**item, **enrichment_data}

            logging.info(f"Successfully enriched and parsed data for item ID: {item_id} with model {model_name}")
            return combined_data

        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON for item ID: {item_id} with model {model_name}. Saving to unparsable.")
            if not os.path.exists(UNPARSABLE_DIR):
                os.makedirs(UNPARSABLE_DIR)
            filename = f"unparsable_{item_id}.txt"
            with open(os.path.join(UNPARSABLE_DIR, filename), 'w', encoding='utf-8') as f:
                f.write(f"---PROMPT---\n{prompt}\n\n---MODEL---\n{model_name}\n\n---RESPONSE---\n{response_content}")
            return None # Stop trying for this item if JSON is unparsable

        except Exception as e:
            # Check for the specific quota exceeded error
            if "429" in str(e) and "token_quota_exceeded" in str(e):
                logging.warning(f"Token quota exceeded for model {model_name}. Rotating to the next model.")
                current_model_index = (current_model_index + 1) % len(MODELS)
                
                # If we have tried all models and are back to the start, give up on this item
                if current_model_index == initial_model_index:
                    logging.error(f"All models have exceeded their token quotas. Cannot process item ID {item_id}. Stopping.")
                    # You might want to exit the script or just skip this item
                    return None # Skip this item
                
                # Wait a bit before retrying with the new model
                time.sleep(2)
                continue # Retry the while loop with the new model
            else:
                logging.error(f"An unexpected error occurred while processing item ID {item_id} with model {model_name}: {e}")
                time.sleep(5) # Wait a bit before processing the next item
                return None # Stop trying for this item on other errors

# --- Main Execution ---
def main():
    """Main function to run the script."""
    # Create the main output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        logging.info(f"Created output directory: {OUTPUT_DIR}")

    # Load all necessary data
    all_items = load_json_file(INPUT_FILE, is_list=True)
    sample_enriched_object = load_json_file(SAMPLE_ENRICHED_FILE)
    
    if not all_items or not sample_enriched_object:
        logging.error("Missing one or more essential input files (transformed_klook_data.json or sample_enriched_object.json). Exiting.")
        return

    # Load existing results to avoid reprocessing
    enriched_results = load_json_file(OUTPUT_FILE, is_list=True)
    processed_ids = {item.get('klook_id') for item in enriched_results if item.get('klook_id')}
    
    logging.info(f"Found {len(enriched_results)} existing results. {len(processed_ids)} unique IDs already processed.")

    # Process each item
    for item in all_items:
        new_data = process_item(item, sample_enriched_object, processed_ids)
        
        if new_data:
            enriched_results.append(new_data)
            save_json_file(enriched_results, OUTPUT_FILE)
            logging.info(f"Appended new data for ID {new_data.get('klook_id')} and saved to {OUTPUT_FILE}.")
            processed_ids.add(new_data.get('klook_id'))

    logging.info("Enrichment process completed.")

if __name__ == "__main__":
    main()
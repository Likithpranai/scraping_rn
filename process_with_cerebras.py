import os
import json
from cerebras.cloud.sdk import Cerebras
import logging
import re

# --- Configuration ---
SCRAPED_DATA_FILE = 'cleaned_activity_data.json'
SAMPLE_DATA_FILE = 'sampleData.json'
TYPE_DEFINITION_FILE = 'activityDetails.ts'
OUTPUT_FILE = 'structured_activity_data.json'
UNPARSABLE_DIR = 'unparsable_results'
# MODEL_NAME = "llama-4-scout-17b-16e-instruct"
# MODEL_NAME = "llama3.3-70b"
# MODEL_NAME = "qwen-3-235b-a22b"
MODEL_NAME = "qwen-3-32b"

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Initialize Cerebras Client ---
try:
    client = Cerebras(api_key="csk-krynjw3xc6kprx4dm4j288ktv5w3rck524m6ddvt2tvfyx4j")
except Exception as e:
    logging.error(f"Failed to initialize Cerebras client: {e}")
    exit(1)

# --- Helper Functions ---
def load_json_file(filename):
    """Loads a JSON file and returns its content."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"File not found: {filename}. Returning empty list or dict.")
        return [] if filename == OUTPUT_FILE else {}
    except json.JSONDecodeError:
        logging.error(f"Could not decode JSON from {filename}. Please check its format.")
        return [] if filename == OUTPUT_FILE else {}

def save_json_file(data, filename):
    """Saves data to a JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def read_file_content(filename):
    """Reads the content of a text file."""
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
        return ""

def create_prompt(scraped_data, type_definition, sample_json):
    """Creates the prompt for the Cerebras API."""
    prompt = f"""
You are an expert data structuring AI. Your task is to convert raw scraped data into a clean, structured JSON object.

**Instructions:**
1.  Analyze the provided "Raw Scraped Data".
2.  Generate a single JSON object that strictly follows the "Target JSON Format".
3.  Use the "Example JSON Object" as a reference for the structure and style.
4.  Do not include any explanations, apologies, or markdown formatting (like ```json) in your response. Output only the raw JSON object.

**Target JSON Format (from a TypeScript interface):**
```typescript
{type_definition}
```

**Example JSON Object:**
```json
{json.dumps(sample_json, indent=2)}
```

**Raw Scraped Data:**
```json
{json.dumps(scraped_data, indent=2)}
```

**Your generated JSON object:**
"""
    return prompt

def process_activity(url, content, type_definition, sample_json, processed_urls):
    """Processes a single activity, calls Cerebras API, and handles the response."""
    if url in processed_urls:
        logging.info(f"Skipping already processed URL: {url}")
        return None

    logging.info(f"Processing URL: {url}")

    prompt = create_prompt({url: content}, type_definition, sample_json)

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=MODEL_NAME,
        )
        response_content = chat_completion.choices[0].message.content

        # Clean up the response in case it's wrapped in markdown
        if response_content.strip().startswith("```json"):
            response_content = response_content.strip()[7:-3].strip()

        # Remove potential "thinking" blocks from the model output
        try:
            response_content = re.sub(r"<think>.*?</think>", "", response_content, flags=re.DOTALL).strip()
        except ImportError:
            logging.warning("Could not import 're' module. Skipping think block removal.")

        
        # Attempt to parse the JSON
        structured_data = json.loads(response_content)
        logging.info(f"Successfully parsed data for URL: {url}")
        return structured_data

    except json.JSONDecodeError:
        logging.error(f"Failed to parse JSON for URL: {url}. Saving to unparsable.")
        filename = url.split('/')[-1] or "unknown_activity"
        with open(os.path.join(UNPARSABLE_DIR, f"{filename}.txt"), 'w') as f:
            f.write(response_content)
        return None
    except Exception as e:
        logging.error(f"An error occurred while processing {url}: {e}")
        return None

# --- Main Execution ---
def main():
    """Main function to run the script."""
    # Load all necessary data
    scraped_data = load_json_file(SCRAPED_DATA_FILE)
    sample_json = load_json_file(SAMPLE_DATA_FILE)
    type_definition = read_file_content(TYPE_DEFINITION_FILE)
    
    if not scraped_data or not sample_json or not type_definition:
        logging.error("Missing one or more essential input files. Exiting.")
        return

    # Load existing results to avoid reprocessing
    structured_results = load_json_file(OUTPUT_FILE)
    processed_urls = {item.get('url') for item in structured_results if item.get('url')}
    
    logging.info(f"Found {len(structured_results)} existing results. {len(processed_urls)} unique URLs processed.")

    # Process each item
    for url, content in scraped_data.items():
        new_data = process_activity(url, content, type_definition, sample_json, processed_urls)
        
        if new_data:
            # Add to results and immediately save
            structured_results.append(new_data)
            save_json_file(structured_results, OUTPUT_FILE)
            logging.info(f"Appended new data for {url} and updated {OUTPUT_FILE}.")
            # Update the set of processed URLs
            processed_urls.add(url)
        

    logging.info("Script finished.")

if __name__ == "__main__":
    if not os.path.exists(UNPARSABLE_DIR):
        os.makedirs(UNPARSABLE_DIR)
    main()

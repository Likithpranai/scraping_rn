#!/usr/bin/env python3
"""
Script to enrich tatler_results.json with specific fields using Cerebras AI API.
"""

import json
import os
import time
import logging
import sys
import requests
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
INPUT_FILE = Path("/Users/likith/Desktop/scraping_rn/tatler/tatler_results.json")
OUTPUT_FILE = Path("/Users/likith/Desktop/scraping_rn/tatler/tatler_results_2.json")
API_KEY = "csk-d6e3nc398njwwpc5w4h8ct5p8d4fxhjy443eh5fj32ywx883"
API_URL = "https://api.cerebras.cloud/v1/chat/completions"  # Cerebras API endpoint

def extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """
    Extract JSON from the Cerebras API response text.
    
    Args:
        response_text: The response text from Cerebras API
        
    Returns:
        Dict[str, Any]: The extracted JSON object
    """
    try:
        # Try to find JSON in code blocks first
        json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # If no code blocks, try to find JSON directly
            json_match = re.search(r'({[\s\S]*})', response_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                # If no JSON-like structure found, use the whole text
                json_str = response_text
        
        # Clean up the JSON string
        # Replace single quotes with double quotes
        json_str = json_str.replace("'", '"')
        
        # Remove trailing commas in lists and objects
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*\]', ']', json_str)
        
        # Parse the JSON
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON: %s", str(e))
        raise ValueError("Invalid JSON format")
    except Exception as e:
        logger.error("Error in extract_json_from_response: %s", str(e))
        raise ValueError("Error processing response")

def create_enrichment_prompt(item: Dict[str, Any]) -> str:
    """
    Create a prompt for enriching a restaurant item with Cerebras AI.
    
    Args:
        item: The restaurant item to enrich
        
    Returns:
        str: The prompt for Cerebras AI
    """
    # Extract relevant information from the item
    name = item.get('source_name', '')
    address = item.get('source_address', '')
    neighborhood = item.get('source_neighbourhood', '')
    price_point = item.get('source_pricepoint', '')
    categories = item.get('source_categories', [])
    description = item.get('enrich_description', '')
    local_tips = item.get('enrich_localTips', '')
    signature_dishes = item.get('enrich_signature', '')
    
    # Create the prompt with exact example output format
    prompt = f"""
    You are an expert restaurant data analyst. Your task is to enrich a restaurant entry with additional data fields.
    
    Here is the restaurant information:
    - Name: {name}
    - Address: {address}
    - Neighborhood: {neighborhood}
    - Price Point: {price_point}
    - Categories: {', '.join(categories) if categories else 'Not specified'}
    - Description: {description}
    - Local Tips: {local_tips}
    - Signature Dishes: {', '.join(signature_dishes) if signature_dishes else 'Not specified'}
    
    Based on this information, please generate the following enrichment fields:
    
    1. enrich_hiddenGemScore: An integer from 0-100 indicating how much of a hidden gem this restaurant is.
       - Score 0-30: Very well-known, mainstream establishments
       - Score 31-60: Somewhat known but not overly popular
       - Score 61-85: Hidden gems that locals know but tourists might miss
       - Score 86-100: True hidden treasures that even locals might not know about
    
    2. enrich_textEmbedding: A comprehensive string that combines the restaurant's name, summary, and highlights into a single text for embedding purposes.
    
    3. enrich_tagsType: A JSON object that distributes 100 points across these categories based on relevance:
       - "Food": [points]
       - "Nature": [points]
       - "Sports": [points]
       - "Leisure": [points]
       - "Shopping": [points]
       - "Wellness": [points]
       - "Adventure": [points]
       - "Nightlife": [points]
       - "Educational": [points]
       - "Hidden Gems": [points]
       - "Photography": [points]
       - "Art & Culture": [points]
       - "Entertainment": [points]
    
    4. enrich_tagsBudget: A JSON object with exactly one of these categories set to 1 and the rest to 0:
       - "Free": [0 or 1]
       - "Budget friendly": [0 or 1]
       - "Moderately priced": [0 or 1]
       - "High-end": [0 or 1]
       - "Luxury": [0 or 1]
    
    5. enrich_tagsGroup: A JSON object that distributes 100 points across these categories based on suitability:
       - "Date": [points]
       - "Kids": [points]
       - "Family": [points]
       - "Friends": [points]
       - "Business": [points]
       - "Colleagues": [points]
    
    Output only a JSON object with these fields, no explanations or markdown formatting.
    
    Example output format (FOLLOW THIS EXACTLY):
    {
      "enrich_hiddenGemScore": 85,
      "enrich_textEmbedding": "Kicho is a renowned Japanese yakitori and tori kappo restaurant located in Central, Hong Kong, known for its premium omakase dining experience featuring Kuro Satsuma chicken from Kagoshima. The restaurant expertly uses charcoal grilling and farm-fresh seasonal Japanese ingredients to deliver a refined 16-course tasting menu, complemented by organic sake and select wines from Miyazaki Prefecture. Reservations are advised due to its popularity and intimate 24-seat setting. Recognized by Tripadvisor's Travelers' Choice and featured in Time Out Hong Kong, it combines tradition with culinary excellence in a sophisticated ambiance.",
      "enrich_tagsType": {
        "Food": 70,
        "Nature": 0,
        "Sports": 0,
        "Leisure": 10,
        "Shopping": 0,
        "Wellness": 0,
        "Adventure": 0,
        "Nightlife": 10,
        "Educational": 0,
        "Hidden Gems": 10,
        "Photography": 0,
        "Art & Culture": 0,
        "Entertainment": 0
      },
      "enrich_tagsBudget": {
        "Free": 0,
        "Budget friendly": 0,
        "Moderately priced": 0,
        "High-end": 1,
        "Luxury": 0
      },
      "enrich_tagsGroup": {
        "Date": 40,
        "Kids": 0,
        "Family": 10,
        "Friends": 30,
        "Business": 20,
        "Colleagues": 0
      }
    }
    """
    
    return prompt

def process_item(item: Dict[str, Any], retry_count: int = 3) -> Dict[str, Any]:
    """
    Process a single item with Cerebras AI and add enrichment fields.
    
    Args:
        item: The item to enrich
        retry_count: Number of retries on failure
        
    Returns:
        The enriched item
    """
    prompt = create_enrichment_prompt(item)
    
    for attempt in range(retry_count):
        try:
            logger.info(f"Processing item: {item.get('source_name', 'Unknown')}")
            
            # Call Cerebras API directly using requests
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-4-scout-17b-16e-instruct",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
                "temperature": 0.2
            }
            
            response = requests.post(API_URL, headers=headers, json=payload)
            
            if response.status_code != 200:
                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                raise Exception(f"API request failed: {response.text}")
                
            # Extract the response text from the JSON response
            response_data = response.json()
            response_content = response_data["choices"][0]["message"]["content"]
            
            # Extract JSON from the response
            try:
                enrichment_data = extract_json_from_response(response_content)
                
                # Validate that all required fields are present
                required_fields = [
                    "enrich_hiddenGemScore",
                    "enrich_textEmbedding",
                    "enrich_tagsType",
                    "enrich_tagsBudget",
                    "enrich_tagsGroup"
                ]
                
                missing_fields = [field for field in required_fields if field not in enrichment_data]
                if missing_fields:
                    logger.warning(f"Missing required fields: {missing_fields}. Retrying... (Attempt {attempt + 1}/{retry_count})")
                    time.sleep(2)  # Wait before retrying
                    continue
                
                # Add enrichment fields to the item
                for key, value in enrichment_data.items():
                    item[key] = value
                
                return item
                
            except ValueError as e:
                logger.warning(f"Failed to extract JSON: {str(e)}. Retrying... (Attempt {attempt + 1}/{retry_count})")
                time.sleep(2) 
                continue
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON response. Retrying... (Attempt {attempt + 1}/{retry_count})")
                logger.debug(f"Response: {response_content}")
                
                # Save unparsable responses for debugging
                unparsable_dir = Path("/Users/likith/Desktop/scraping_rn/tatler/unparsable_responses")
                unparsable_dir.mkdir(exist_ok=True)
                unparsable_file = unparsable_dir / f"unparsable_{item.get('source_name', 'unknown').replace(' ', '_')}_{attempt}.txt"
                with open(unparsable_file, 'w', encoding='utf-8') as f:
                    f.write(f"---PROMPT---\n{prompt}\n\n---RESPONSE---\n{response_content}")
                
                time.sleep(2)  # Wait before retrying
                continue
                
        except Exception as e:
            logger.error(f"Error calling Cerebras API: {str(e)}. Retrying... (Attempt {attempt + 1}/{retry_count})")
            time.sleep(2)  # Wait before retrying
    
    logger.error(f"Failed to enrich item after {retry_count} attempts: {item.get('source_name', 'Unknown')}")
    return item  # Return original item if all retries fail

def main():
    """Main function to process the tatler_results.json file."""
    if not INPUT_FILE.exists():
        logger.error("Input file not found: %s", str(INPUT_FILE))
        sys.exit(1)
    
    try:
        # Load input data
        logger.info("Loading data from %s", str(INPUT_FILE))
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.error("Input data is not a list")
            sys.exit(1)
        
        # Process each item
        logger.info("Processing %d items", len(data))
        enriched_data = []
        
        for i, item in enumerate(data):
            try:
                enriched_item = process_item(item)
                enriched_data.append(enriched_item)
                logger.info("Processed item %d/%d: %s", i+1, len(data), item.get('source_name', 'Unknown'))
                
                # Add a small delay between API calls to avoid rate limiting
                if i < len(data) - 1:  # Don't sleep after the last item
                    time.sleep(1)
                    
            except Exception as e:
                # Use old-style formatting to avoid issues with % in error messages
                logger.error("Error processing item %d: %s", i+1, str(e))
                
                # Save the problematic item for debugging
                error_dir = Path("/Users/likith/Desktop/scraping_rn/tatler/error_items")
                error_dir.mkdir(exist_ok=True)
                with open(error_dir / "error_item_{}.json".format(i), 'w', encoding='utf-8') as f:
                    json.dump(item, f, indent=2)
                
                # Add the original item if processing fails
                enriched_data.append(item)
        
        # Save enriched data
        logger.info("Saving enriched data to %s", str(OUTPUT_FILE))
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, indent=2, ensure_ascii=False)
        
        logger.info("Enrichment completed successfully")
        
    except Exception as e:
        logger.error("An error occurred: %s", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()

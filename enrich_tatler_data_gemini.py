#!/usr/bin/env python3
"""
Script to enrich tatler_results.json with specific fields using Google Gemini AI API.
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
API_KEY = "AIzaSyANPZ22O3GUeId9x3NVcrzjAieb_pWkVV4"
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent"

def extract_json_from_response(response_text: str) -> Dict[str, Any]:
    """
    Extract JSON from the Gemini API response text.
    
    Args:
        response_text: The response text from Gemini API
        
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
    Create a prompt for enriching a restaurant item with Gemini AI.
    
    Args:
        item: The restaurant item to enrich
        
    Returns:
        str: The prompt for Gemini AI
    """
    # Extract relevant information from the item
    name = item.get('source_name', '')
    address = item.get('source_address', '')
    neighborhood = item.get('source_neighbourhood', '')
    price_point = item.get('source_pricepoint', '')
    categories = item.get('source_categories', [])
    description = item.get('enrich_description', '')
    local_tips = item.get('enrich_localTips', '')
    signature_dishes = item.get('enrich_signature', [])
    
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
    Process a single item with Gemini AI and add enrichment fields.
    
    Args:
        item: The item to enrich
        retry_count: Number of retries on failure
        
    Returns:
        The enriched item
    """
    prompt = create_enrichment_prompt(item)
    item_name = item.get('source_name', 'Unknown')
    
    # Create debug directories
    debug_dir = Path("/Users/likith/Desktop/scraping_rn/tatler/debug")
    debug_dir.mkdir(exist_ok=True)
    
    # Save the prompt for debugging
    with open(debug_dir / ("prompt_" + item_name.replace("/", "_") + ".txt"), 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    for attempt in range(retry_count):
        try:
            # Avoid string formatting in logs
            logger.info("Processing item: " + item_name)
            
            # Call Gemini API using requests
            headers = {
                "Content-Type": "application/json"
            }
            
            # Construct the API URL with the API key
            url = API_URL + "?key=" + API_KEY
            
            payload = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1024
                }
            }
            
            # Print API request details for debugging
            print("\nAPI URL: " + url)
            print("API Key: " + API_KEY[:5] + "..." + API_KEY[-5:])
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                
                # Save full response for debugging
                with open(debug_dir / ("response_full_" + item_name.replace("/", "_") + ".txt"), 'w', encoding='utf-8') as f:
                    f.write("Status Code: " + str(response.status_code) + "\n\n")
                    f.write("Headers:\n" + str(response.headers) + "\n\n")
                    f.write("Content:\n" + response.text)
                
                if response.status_code != 200:
                    # Avoid string formatting
                    error_msg = "API request failed with status code: " + str(response.status_code)
                    print(error_msg)
                    print("Response: " + response.text)
                    logger.error(error_msg)
                    raise Exception("API request failed: " + response.text[:100])
                    
                # Extract the response text from the JSON response
                try:
                    response_data = response.json()
                except json.JSONDecodeError as e:
                    print("JSON decode error: " + str(e))
                    print("Response text: " + response.text[:200])
                    raise ValueError("Invalid JSON in API response")
                
                # Save parsed JSON response for debugging
                with open(debug_dir / ("response_json_" + item_name.replace("/", "_") + ".json"), 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, indent=2)
                
                # Extract content from Gemini API response
                try:
                    response_content = response_data["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # Save extracted content for debugging
                    with open(debug_dir / ("content_" + item_name.replace("/", "_") + ".txt"), 'w', encoding='utf-8') as f:
                        f.write(response_content)
                        
                except (KeyError, IndexError) as e:
                    print("Key/Index error: " + str(e))
                    print("Response data: " + str(response_data))
                    logger.error("Failed to extract content from Gemini API response: " + str(e))
                    raise ValueError("Invalid response structure from Gemini API")
                
                # Extract JSON from the response
                try:
                    enrichment_data = extract_json_from_response(response_content)
                    
                    # Save extracted JSON for debugging
                    with open(debug_dir / ("extracted_json_" + item_name.replace("/", "_") + ".json"), 'w', encoding='utf-8') as f:
                        json.dump(enrichment_data, f, indent=2)
                    
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
                        print("Missing fields: " + str(missing_fields))
                        logger.warning("Missing required fields: " + str(missing_fields))
                        time.sleep(2)  # Wait before retrying
                        continue
                    
                    # Add enrichment fields to the item
                    for key, value in enrichment_data.items():
                        item[key] = value
                    
                    print("Successfully enriched item: " + item_name)
                    return item
                    
                except ValueError as e:
                    print("JSON extraction error: " + str(e))
                    logger.warning("Failed to extract JSON: " + str(e))
                    time.sleep(2)  # Wait before retrying
                    continue
                    
            except requests.exceptions.RequestException as e:
                print("Request exception: " + str(e))
                logger.error("Request error: " + str(e))
                time.sleep(5)  # Longer wait for network issues
                continue
                
        except Exception as e:
            print("General exception: " + str(e))
            logger.error("Error in process_item: " + str(e))
            time.sleep(2)  # Wait before retrying
    
    print("Failed to enrich item after all attempts: " + item_name)
    logger.error("Failed to enrich item after " + str(retry_count) + " attempts: " + item_name)
    return item  # Return original item if all retries fail

def main():
    """Main function to process the tatler_results.json file."""
    if not INPUT_FILE.exists():
        logger.error("Input file not found: " + str(INPUT_FILE))
        sys.exit(1)
    
    try:
        # Load input data
        logger.info("Loading data from " + str(INPUT_FILE))
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.error("Input data is not a list")
            sys.exit(1)
        
        # Process each item
        logger.info("Processing " + str(len(data)) + " items")
        enriched_data = []
        
        for i, item in enumerate(data):
            try:
                enriched_item = process_item(item)
                enriched_data.append(enriched_item)
                item_name = item.get('source_name', 'Unknown')
                # Avoid string formatting completely
                logger.info("Processed item " + str(i+1) + "/" + str(len(data)) + ": " + item_name)
                
                # Add a small delay between API calls to avoid rate limiting
                if i < len(data) - 1:  # Don't sleep after the last item
                    time.sleep(1)
                    
            except Exception:
                # Avoid string formatting completely
                logger.error("Error processing item " + str(i+1))
                
                # Save the problematic item for debugging
                error_dir = Path("/Users/likith/Desktop/scraping_rn/tatler/error_items")
                error_dir.mkdir(exist_ok=True)
                error_file = error_dir / ("error_item_" + str(i) + ".json")
                with open(error_file, 'w', encoding='utf-8') as f:
                    json.dump(item, f, indent=2)
                
                # Add the original item if processing fails
                enriched_data.append(item)
        
        # Save enriched data
        logger.info("Saving enriched data to " + str(OUTPUT_FILE))
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(enriched_data, f, indent=2, ensure_ascii=False)
        
        logger.info("Enrichment completed successfully")
        
    except Exception:
        logger.error("An error occurred during processing")
        sys.exit(1)

if __name__ == "__main__":
    main()

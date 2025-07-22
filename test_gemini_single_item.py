#!/usr/bin/env python3
"""
Test script to process a single item from tatler_results.json with Gemini API
"""

import json
import os
import time
import sys
from pathlib import Path
import requests

# Constants
INPUT_FILE = Path("/Users/likith/Desktop/scraping_rn/tatler/tatler_results.json")
API_KEY = "AIzaSyANPZ22O3GUeId9x3NVcrzjAieb_pWkVV4"
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent"

def create_enrichment_prompt(item):
    """
    Create a prompt for enriching a restaurant item with Gemini AI.
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

def extract_json_from_response(response_text):
    """
    Extract JSON from the Gemini API response text.
    """
    # Try to find JSON in code blocks first
    import re
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

def process_single_item():
    """Process a single item from tatler_results.json"""
    
    # Create debug directory
    debug_dir = Path("/Users/likith/Desktop/scraping_rn/tatler/debug")
    debug_dir.mkdir(exist_ok=True)
    
    # Load input data
    print(f"Loading data from {INPUT_FILE}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list) or len(data) == 0:
        print("Input data is not a list or is empty")
        sys.exit(1)
    
    # Get the first item
    item = data[0]
    item_name = item.get('source_name', 'Unknown')
    print(f"Processing item: {item_name}")
    
    # Create prompt
    prompt = create_enrichment_prompt(item)
    
    # Save prompt for debugging
    prompt_file = debug_dir / "prompt.txt"
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    print(f"Saved prompt to {prompt_file}")
    
    # Call Gemini API
    headers = {
        "Content-Type": "application/json"
    }
    
    url = f"{API_URL}?key={API_KEY}"
    
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
    
    print(f"Sending request to Gemini API...")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # Save full response
        response_file = debug_dir / "response_full.txt"
        with open(response_file, 'w', encoding='utf-8') as f:
            f.write(f"Status Code: {response.status_code}\n\n")
            f.write(f"Headers:\n{response.headers}\n\n")
            f.write(f"Content:\n{response.text}")
        print(f"Saved full response to {response_file}")
        
        if response.status_code != 200:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)
        
        # Parse response
        response_data = response.json()
        
        # Save parsed response
        json_file = debug_dir / "response.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2)
        print(f"Saved parsed response to {json_file}")
        
        # Extract content
        try:
            response_content = response_data["candidates"][0]["content"]["parts"][0]["text"]
            
            # Save content
            content_file = debug_dir / "content.txt"
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(response_content)
            print(f"Saved content to {content_file}")
            
            # Extract JSON
            try:
                enrichment_data = extract_json_from_response(response_content)
                
                # Save extracted JSON
                extracted_file = debug_dir / "extracted.json"
                with open(extracted_file, 'w', encoding='utf-8') as f:
                    json.dump(enrichment_data, f, indent=2)
                print(f"Saved extracted JSON to {extracted_file}")
                
                # Validate fields
                required_fields = [
                    "enrich_hiddenGemScore",
                    "enrich_textEmbedding",
                    "enrich_tagsType",
                    "enrich_tagsBudget",
                    "enrich_tagsGroup"
                ]
                
                missing_fields = [field for field in required_fields if field not in enrichment_data]
                if missing_fields:
                    print(f"Missing required fields: {missing_fields}")
                else:
                    print("All required fields present!")
                    
                    # Add enrichment fields to the item
                    enriched_item = item.copy()
                    for key, value in enrichment_data.items():
                        enriched_item[key] = value
                    
                    # Save enriched item
                    enriched_file = debug_dir / "enriched_item.json"
                    with open(enriched_file, 'w', encoding='utf-8') as f:
                        json.dump(enriched_item, f, indent=2)
                    print(f"Saved enriched item to {enriched_file}")
                    
            except Exception as e:
                print(f"Error extracting JSON: {e}")
                print(f"Response content: {response_content[:200]}...")
                
        except Exception as e:
            print(f"Error extracting content: {e}")
            print(f"Response data: {json.dumps(response_data, indent=2)}")
            
    except Exception as e:
        print(f"Error calling API: {e}")

if __name__ == "__main__":
    process_single_item()

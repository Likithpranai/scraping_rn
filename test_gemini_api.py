#!/usr/bin/env python3
"""
Simple test script for Google Gemini API
"""

import requests
import json

API_KEY = "AIzaSyANPZ22O3GUeId9x3NVcrzjAieb_pWkVV4"
API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent"

def test_gemini_api():
    """Test the Gemini API with a simple prompt"""
    
    # Simple prompt
    prompt = "Hello, please respond with a simple JSON object with the following structure: {\"test\": \"success\"}"
    
    # API request headers
    headers = {
        "Content-Type": "application/json"
    }
    
    # Construct the API URL with the API key
    url = f"{API_URL}?key={API_KEY}"
    
    # Request payload
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
    
    print(f"Sending request to: {url}")
    print(f"API Key (first/last 5 chars): {API_KEY[:5]}...{API_KEY[-5:]}")
    
    try:
        # Send the request
        response = requests.post(url, headers=headers, json=payload)
        
        # Print response details
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            # Parse the response
            response_data = response.json()
            print(f"Response data: {json.dumps(response_data, indent=2)}")
            
            # Extract the response text
            try:
                response_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
                print(f"Response text: {response_text}")
            except (KeyError, IndexError) as e:
                print(f"Error extracting response text: {e}")
                print(f"Response structure: {response_data}")
        else:
            print(f"Error response: {response.text}")
    
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_gemini_api()

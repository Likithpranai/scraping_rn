#!/usr/bin/env python3
import json
import os
import re

def fix_timeout_json():
    """
    Fix the timeout_bar_final.json file which has structural issues:
    - The file appears to have a nested array starting at line 1422
    - This breaks the overall JSON structure
    
    This improved version uses a more robust approach to reconstruct the JSON.
    """
    input_file = '/Users/likith/Desktop/scraping_rn/timeout/timeout_bar_final.json'
    output_file = '/Users/likith/Desktop/scraping_rn/timeout/timeout_bar_fixed.json'
    
    print(f"Reading file: {input_file}")
    
    # Read the entire file content
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("Analyzing JSON structure...")
    
    # Approach: Extract all individual JSON objects and reconstruct the array
    
    # First, check if the file starts with an array opening bracket
    if not content.strip().startswith('['):
        print("Error: File doesn't start with an array '['")
        return
    
    # Use regex to find all complete JSON objects in the file
    # This pattern looks for objects starting with { and ending with }
    object_pattern = re.compile(r'\s*(\{[^{]*?(?:\{[^{]*?\}[^{]*?)*\})\s*', re.DOTALL)
    objects = object_pattern.findall(content)
    
    print(f"Found {len(objects)} potential JSON objects")
    
    # Validate each object and collect valid ones
    valid_objects = []
    for i, obj in enumerate(objects):
        try:
            # Try to parse the object as JSON
            json_obj = json.loads(obj)
            valid_objects.append(obj)
        except json.JSONDecodeError as e:
            print(f"Object {i} is invalid JSON: {e}")
            # Print a snippet of the problematic object for debugging
            print(f"Snippet: {obj[:100]}...")
    
    print(f"Found {len(valid_objects)} valid JSON objects")
    
    # Reconstruct the JSON array with valid objects
    reconstructed_json = "[\n  " + ",\n  ".join(valid_objects) + "\n]"
    
    # Validate the reconstructed JSON
    try:
        parsed_json = json.loads(reconstructed_json)
        print(f"Reconstructed JSON is valid with {len(parsed_json)} objects!")
    except json.JSONDecodeError as e:
        print(f"Error: Reconstructed JSON is still invalid: {e}")
        # Save the partially reconstructed content for inspection
        with open(output_file + '.partial', 'w', encoding='utf-8') as f:
            f.write(reconstructed_json)
        print(f"Partially reconstructed content saved to {output_file}.partial")
        return
    
    # Save the fixed JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        # Use json.dump to ensure proper formatting
        json.dump(parsed_json, f, indent=2, ensure_ascii=False)
    
    print(f"Fixed JSON saved to {output_file}")
    
    # Additional validation: Check if the number of objects matches what we expect
    print(f"Number of objects in the fixed JSON: {len(parsed_json)}")

if __name__ == "__main__":
    fix_timeout_json()

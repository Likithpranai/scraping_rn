#!/usr/bin/env python3
import json
import os
import re

def fix_timeout_json():
    """
    Fix the timeout_bar_final.json file which has structural issues:
    - The file appears to have a nested array starting at line 1422
    - This breaks the overall JSON structure
    """
    input_file = '/Users/likith/Desktop/scraping_rn/timeout/timeout_bar_final.json'
    output_file = '/Users/likith/Desktop/scraping_rn/timeout/timeout_bar_fixed.json'
    
    print(f"Reading file: {input_file}")
    
    # Read the entire file content
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # First, let's try to identify the structure by examining the content
    print("Analyzing JSON structure...")
    
    # Check if the file starts with an array
    if not content.strip().startswith('['):
        print("Error: File doesn't start with an array '['")
        return
    
    # Find the position where the nested array starts
    nested_array_match = re.search(r',\s*\[\s*\{', content)
    if not nested_array_match:
        print("Could not find the nested array pattern")
        return
    
    nested_array_pos = nested_array_match.start()
    print(f"Found nested array starting at position {nested_array_pos}")
    
    # Extract the first part (before the nested array) and the nested array part
    first_part = content[:nested_array_pos]
    nested_array_part = content[nested_array_pos+1:]  # +1 to skip the comma
    
    # Check if the first part ends with a closing brace and the nested part starts with an opening bracket
    if not first_part.rstrip().endswith('}'):
        print("Error: First part doesn't end with '}'")
        return
    
    if not nested_array_part.lstrip().startswith('['):
        print("Error: Nested part doesn't start with '['")
        return
    
    # Fix approach: Convert the nested array items into regular items in the main array
    # First, remove the trailing closing brace from the first part
    first_part = first_part.rstrip()
    if first_part.endswith('},'):
        first_part = first_part[:-2] + ','  # Remove the closing brace and keep the comma
    elif first_part.endswith('}'):
        first_part = first_part[:-1] + ','  # Remove the closing brace and add a comma
    
    # Remove the opening and closing brackets of the nested array
    nested_array_part = nested_array_part.strip()
    if nested_array_part.startswith('['):
        nested_array_part = nested_array_part[1:]
    if nested_array_part.endswith(']'):
        nested_array_part = nested_array_part[:-1]
    
    # Combine the parts to form a valid JSON array
    fixed_content = first_part + nested_array_part
    
    # Ensure the JSON is properly closed
    if not fixed_content.rstrip().endswith(']'):
        fixed_content = fixed_content.rstrip() + '\n]'
    
    # Validate the fixed JSON
    try:
        json.loads(fixed_content)
        print("Fixed JSON is valid!")
    except json.JSONDecodeError as e:
        print(f"Error: Fixed JSON is still invalid: {e}")
        # Save the partially fixed content for inspection
        with open(output_file + '.partial', 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"Partially fixed content saved to {output_file}.partial")
        return
    
    # Save the fixed JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"Fixed JSON saved to {output_file}")
    
    # Count the number of objects in the fixed JSON
    fixed_json = json.loads(fixed_content)
    print(f"Number of objects in the fixed JSON: {len(fixed_json)}")

if __name__ == "__main__":
    fix_timeout_json()

#!/usr/bin/env python3
import json
import os
import re

def fix_json_file(input_path, output_path):
    """
    Fix the JSON structure in wanderlog_bar_final.json using a more robust approach
    """
    print(f"Reading file: {input_path}")
    
    try:
        # Read the entire file as text
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # First attempt: Try to parse as is
        try:
            data = json.loads(content)
            print("JSON is already valid! No fixes needed.")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except json.JSONDecodeError as e:
            print(f"JSON is invalid: {e}")
        
        # Second approach: Manual reconstruction of the JSON structure
        print("Attempting manual reconstruction of the JSON structure...")
        
        # Extract the top-level source_url
        source_url_match = re.search(r'"source_url":\s*"([^"]+)"', content)
        source_url = source_url_match.group(1) if source_url_match else ""
        
        # Extract all bar entries - each starts with {"source_url": and ends with a matching }
        bar_entries = []
        
        # Find all potential bar entries
        bar_pattern = re.compile(r'\{\s*"source_url":\s*"[^"]+".*?(?=\{\s*"source_url":|$)', re.DOTALL)
        matches = list(bar_pattern.finditer(content))
        
        for i, match in enumerate(matches):
            entry_text = match.group(0).strip()
            
            # Make sure the entry ends with a closing brace
            if not entry_text.rstrip().endswith('}'):
                entry_text += '}'
                
            # Remove trailing commas before closing braces
            entry_text = re.sub(r',\s*}', '}', entry_text)
            
            # Try to parse this entry
            try:
                entry_json = json.loads(entry_text)
                bar_entries.append(entry_json)
                print(f"Successfully parsed entry {i+1}")
            except json.JSONDecodeError as e:
                print(f"Failed to parse entry {i+1}: {e}")
                # Try to fix common issues
                try:
                    # Fix missing quotes around property names
                    fixed_text = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', entry_text)
                    # Fix trailing commas in objects
                    fixed_text = re.sub(r',\s*}', '}', fixed_text)
                    entry_json = json.loads(fixed_text)
                    bar_entries.append(entry_json)
                    print(f"Fixed and parsed entry {i+1}")
                except json.JSONDecodeError:
                    print(f"Could not fix entry {i+1}, skipping")
        
        # Create the final JSON structure
        result = {
            "source_url": source_url,
            "bars": bar_entries
        }
        
        # Write the fixed JSON to the output file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Fixed JSON written to {output_path}")
        
        # Validate the output file
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                json.load(f)
            print("Output JSON is valid!")
            return True
        except json.JSONDecodeError as e:
            print(f"Output JSON is invalid: {e}")
            return False
            
    except Exception as e:
        print(f"Error fixing JSON file: {e}")
        return False

if __name__ == "__main__":
    input_file = "/Users/likith/Desktop/scraping_rn/wanderlog/wanderlog_bar_final.json"
    output_file = "/Users/likith/Desktop/scraping_rn/wanderlog/wanderlog_bar_fixed.json"
    
    success = fix_json_file(input_file, output_file)
    
    if success:
        print("JSON file fixed successfully!")
    else:
        print("Failed to fix JSON file.")

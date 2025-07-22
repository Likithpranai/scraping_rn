#!/usr/bin/env python3
import json
import os

def fix_json_file(input_path, output_path):
    """
    Fix the JSON structure in wanderlog_bar_final.json
    
    Issues to fix:
    1. Nested 'bars' array inside the main 'bars' array
    2. Incomplete JSON structure at the end
    """
    print(f"Reading file: {input_path}")
    
    try:
        # Read the entire file as text first
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse it as JSON to see if it's valid
        try:
            data = json.loads(content)
            print("JSON is already valid! No fixes needed.")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except json.JSONDecodeError as e:
            print(f"JSON is invalid: {e}")
            
        # Manual fix for the specific issues we've identified
        print("Attempting to fix JSON structure...")
        
        # Split content into lines for easier manipulation
        lines = content.split('\n')
        
        # Find the problematic nested "bars" array
        nested_bars_index = -1
        for i, line in enumerate(lines):
            if '"source_url": "https://wanderlog.com/list/geoCategory/685/best-bars-and-drinks-in-hong-kong",' in line and '"bars": [' in lines[i+1]:
                nested_bars_index = i
                break
        
        if nested_bars_index > 0:
            print(f"Found nested 'bars' array at line {nested_bars_index+1}")
            
            # Extract the items from the nested bars array
            nested_items = []
            nesting_level = 0
            in_nested_array = False
            nested_item_start = -1
            
            for i in range(nested_bars_index + 2, len(lines)):
                line = lines[i].strip()
                
                if line.startswith("{"):
                    if not in_nested_array:
                        in_nested_array = True
                        nested_item_start = i
                    nesting_level += 1
                elif line.startswith("}"):
                    nesting_level -= 1
                    if nesting_level == 0 and in_nested_array:
                        # Extract the complete nested item
                        item_lines = lines[nested_item_start:i+1]
                        nested_items.append("\n".join(item_lines))
                        in_nested_array = False
                
                # Check if we've reached the end of the nested array
                if line.startswith("]") and nesting_level == 0 and not in_nested_array:
                    break
            
            # Remove the problematic object with the nested bars array
            fixed_lines = lines[:nested_bars_index]
            
            # Add the extracted items directly to the main array
            for item in nested_items:
                fixed_lines.append(item + ",")
            
            # Make sure we have proper JSON closure
            fixed_lines.append("  ]")
            fixed_lines.append("}")
            
            # Join the lines back together
            fixed_content = "\n".join(fixed_lines)
            
            # Validate the fixed JSON
            try:
                json.loads(fixed_content)
                print("Fixed JSON is valid!")
                
                # Write the fixed content to the output file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"Fixed JSON written to {output_path}")
                return True
            except json.JSONDecodeError as e:
                print(f"Fixed JSON is still invalid: {e}")
                return False
        else:
            print("Could not find the nested 'bars' array.")
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

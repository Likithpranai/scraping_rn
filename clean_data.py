import json
import re
import os

# Define the input and output file names
input_filename = 'scraped_activity_data.json'
output_filename = 'cleaned_activity_data.json'

def clean_json_values(input_file, output_file):
    """
    Reads a JSON file, cleans its string values using regex,
    and writes the result to a new JSON file.
    """
    # Check if the input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    # Read the original JSON data from the file
    with open(input_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from '{input_file}': {e}")
            return

    # Create a new dictionary to hold the cleaned data
    cleaned_data = {}

    # Define the regex patterns to find and delete content.
    # re.DOTALL is used to make '.' match newline characters as well.
    # The patterns are designed to keep the start and end markers.
    
    # Pattern 1: Deletes content BETWEEN 'usage_images' and 'latest_best_review'
    pattern1 = re.compile(r'(usage_images).*?(latest_best_review)', re.DOTALL)
    
    # Pattern 2: Deletes content BETWEEN 'chat_info' and '{name:["activity_internal_link"]}'
    # We escape special regex characters like {, }, [, ]
    pattern2 = re.compile(r'(chat_info).*?(\{name:\["activity_internal_link"\]\})', re.DOTALL)

    # Iterate over each key-value pair in the loaded data
    for key, value in data.items():
        # Ensure the value is a string before applying regex
        if isinstance(value, str):
            # Apply the first regex substitution
            # The replacement '\1\2' keeps the captured start (group 1) and end (group 2) markers
            cleaned_value = re.sub(pattern1, r'\1\2', value)
            
            # Apply the second regex substitution on the result of the first
            cleaned_value = re.sub(pattern2, r'\1\2', cleaned_value)

            # Decode Unicode escape sequences (like \u002F -> /)
            # This handles both \u002F and \\u002F patterns
            try:
                # First, handle double-escaped sequences (\\u002F -> \u002F)
                cleaned_value = cleaned_value.replace('\\\\u', '\\u')
                
                # Then decode the Unicode escape sequences
                cleaned_value = cleaned_value.encode().decode('unicode_escape')
            except (UnicodeDecodeError, UnicodeEncodeError) as e:
                print(f"Warning: Could not decode Unicode escapes in key '{key}': {e}")
                # If decoding fails, keep the cleaned value as is
            
            # Store the cleaned value in our new dictionary
            cleaned_data[key] = cleaned_value
        else:
            # If the value is not a string, keep it as is
            cleaned_data[key] = value

    # Write the cleaned dictionary to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        # Use indent=4 for pretty-printing the JSON
        json.dump(cleaned_data, f, ensure_ascii=False, indent=4)

    print(f"Successfully cleaned the data and saved it to '{output_file}'")

# Run the cleaning function
clean_json_values(input_filename, output_filename)
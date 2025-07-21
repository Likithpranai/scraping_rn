import re
import json

def extract_klook_data(file_path):
    """
    Extracts all text between 'activityDetail:' and ',"dynamic_component"'.

    Args:
        file_path (str): The path to the input text file.

    Returns:
        str: The extracted text, or None if not found.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to find all text between activityDetail: and ,"dynamic_component"
        # re.DOTALL allows '.' to match newline characters
        match = re.search(r'activityDetail:(.*?),"dynamic_component"', content, re.DOTALL)

        if match:
            # Return the captured group (the text between the markers)
            return match.group(1)
        else:
            print("No match found in the file.")
            return None

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return None

if __name__ == '__main__':
    # Path to your file
    input_file = 'activity_test_1line.txt'
    
    # Extract and print the relevant data
    filtered_data = extract_klook_data(input_file)
    
    if filtered_data:
        print("Successfully extracted data:")
        print(filtered_data)
        
        # Optionally, save the filtered data to a new file
        with open('filtered_activity_data.txt', 'w', encoding='utf-8') as out_file:
            out_file.write(filtered_data)
        print("\nFiltered data saved to 'filtered_activity_data.txt'")
    else:
        print("Could not extract data from the file.")


import json
import os

def filter_activity_links(input_file, output_file):
    """
    Filter links to get only activity links and convert relative URLs to full URLs.
    
    Args:
        input_file (str): Path to the input JSON file
        output_file (str): Path to the output JSON file
    """
    
    # Read the input JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract all links from the data
    all_links = data.get('all_links', [])
    
    # Filter and process activity links
    filtered_links = []
    
    for link in all_links:
        # Check if link starts with "/activity" or "https://www.klook.com/activity"
        if link.startswith('/activity'):
            # Convert relative URL to full URL
            full_url = f"https://www.klook.com{link}"
            filtered_links.append(full_url)
        elif link.startswith('https://www.klook.com/activity'):
            # Already a full URL, add as is
            filtered_links.append(link)
    
    # Remove duplicates while preserving order
    unique_filtered_links = []
    seen = set()
    for link in filtered_links:
        if link not in seen:
            unique_filtered_links.append(link)
            seen.add(link)
    
    # Create output data structure
    output_data = {
        'total_activity_links': len(unique_filtered_links),
        'original_total_links': data.get('total_links_found', 0),
        'filtered_activity_links': unique_filtered_links
    }
    
    # Write the filtered data to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Filtered {len(unique_filtered_links)} activity links from {len(all_links)} total links")
    print(f"Output saved to: {output_file}")
    
    return unique_filtered_links

def main():
    # Define file paths
    input_file = 'scraped_links_simple.json'
    output_file = 'filtered_activity_links.json'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        return
    
    # Filter the links
    try:
        filtered_links = filter_activity_links(input_file, output_file)
        
        # Print some sample links
        print(f"\nSample filtered links (first 10):")
        for i, link in enumerate(filtered_links[:10]):
            print(f"{i+1}. {link}")
            
        if len(filtered_links) > 10:
            print(f"... and {len(filtered_links) - 10} more links")
            
    except Exception as e:
        print(f"Error processing files: {e}")

if __name__ == "__main__":
    main()

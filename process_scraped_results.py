import requests
import json
import time
import re
import os

def extract_klook_data(content):
    """
    Extracts all text between 'activityDetail:' and ',"dynamic_component"'.

    Args:
        content (str): The content to search within.

    Returns:
        str: The extracted text, or None if not found.
    """
    try:
        # Regex to find all text between activityDetail: and ,"dynamic_component"
        # re.DOTALL allows '.' to match newline characters

        with open('temp.html', 'w', encoding='utf-8') as f:
            f.write(content)
        match = re.search(r'activityDetail:(.*?),\"dynamic_component\"', content, re.DOTALL)

        if match:
            # Return the captured group (the text between the markers)
            return match.group(1)
        else:
            print("No match found in the content.")
            return None

    except Exception as e:
        print(f"An unexpected error occurred during extraction: {e}")

    return None

def main():
    # --- Configuration ---
    jobs_filename = 'jobs.json'
    output_filename = 'scraped_activity_data.json'
    
    # --- Load URLs from jobs.json ---
    try:
        with open(jobs_filename, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
    except FileNotFoundError:
        print(f"Error: '{jobs_filename}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not parse '{jobs_filename}'.")
        return

    print(f"Loaded {len(jobs)} jobs from '{jobs_filename}'.")

    # --- Load existing data to avoid re-scraping ---
    if os.path.exists(output_filename):
        try:
            with open(output_filename, 'r', encoding='utf-8') as f:
                results_data = json.load(f)
            print(f"Loaded {len(results_data)} existing results from '{output_filename}'.")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load existing data from '{output_filename}'. Starting fresh. Error: {e}")
            results_data = {}
    else:
        results_data = {}


    # --- Process Results ---
    processed_count = 0
    failed_count = 0
    skipped_count = 0

    for job in jobs:
        try:
            status_url = job.get('statusUrl')
            original_url = job.get('url')

            if not status_url or not original_url:
                print(f"Warning: Skipping job due to missing 'statusUrl' or 'originalUrl': {job}")
                failed_count += 1
                continue

            # --- Skip if already processed ---
            if original_url in results_data and results_data[original_url] is not None and not results_data[original_url] == "Failed to scrape or empty body":
                print(f"Skipping already processed URL: {original_url}")
                skipped_count += 1
                continue

            print(f"Fetching result from: {status_url}")
            response = requests.get(status_url)
            response.raise_for_status() # Raise an exception for bad status codes
            result = response.json()

            # The actual HTML content is in result['response']['body']
            html_text = result.get('response', {}).get('body')

            if not html_text:
                print(f"Warning: No 'body' content in result for {original_url}")
                failed_count += 1
                results_data[original_url] = "Failed to scrape or empty body"
            else:
                filtered_data = extract_klook_data(html_text)
                if filtered_data:
                    results_data[original_url] = filtered_data
                else:
                    print(f"Warning: No data could be extracted for {original_url}")
                    results_data[original_url] = None # No data could be extracted
            
            processed_count += 1
            
            # --- Save Processed Data Incrementally ---
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=4, ensure_ascii=False)
            print(f"Saved data for {original_url} to '{output_filename}'")


            # Add a small delay to be respectful to the server
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching result from {status_url}: {e}")
            failed_count += 1
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error processing result from {status_url}: {e}")
            failed_count += 1
        except Exception as e:
            print(f"An unexpected error occurred for {status_url}: {e}")
            failed_count += 1

    print(f"\nProcessing complete.")
    print(f"Successfully processed: {processed_count}")
    print(f"Skipped (already existed): {skipped_count}")
    print(f"Failed or missing: {failed_count}")
    print(f"All extracted data saved to '{output_filename}'")

if __name__ == '__main__':
    main()

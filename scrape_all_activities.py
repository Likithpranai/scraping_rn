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
        match = re.search(r'activityDetail:(.*?),"dynamic_component"', content, re.DOTALL)

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
    # --- State and Progress Files ---
    output_filename = 'scraped_activity_data.json'
    job_state_filename = 'scraper_job_state.json'

    # --- Load Existing Progress ---
    results_data = {}
    if os.path.exists(output_filename):
        with open(output_filename, 'r', encoding='utf-8') as f:
            try:
                results_data = json.load(f)
                print(f"Loaded {len(results_data)} existing results from '{output_filename}'.")
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from '{output_filename}'. Starting fresh.")
    
    processed_urls = set(results_data.keys())

    # Load URLs from filtered_activity_links.json
    try:
        with open('filtered_activity_links.json', 'r') as f:
            data = json.load(f)
            initial_url_list = data.get('filtered_activity_links', [])
    except FileNotFoundError:
        print("Error: filtered_activity_links.json not found.")
        return
    except json.JSONDecodeError:
        print("Error: Could not decode JSON from filtered_activity_links.json.")
        return

    # Filter out already processed URLs
    url_list = [url for url in initial_url_list if url not in processed_urls]

    if not url_list:
        print("All URLs have already been processed. Nothing to do.")
        return

    print(f"Loaded {len(initial_url_list)} total URLs. {len(url_list)} URLs remaining to process.")

    # --- ScraperAPI Job Handling ---
    job_id = None
    status_url = None

    # Check if a job is already in progress
    # if os.path.exists(job_state_filename):
    #     try:
    #         with open(job_state_filename, 'r') as f:
    #             job_state = json.load(f)
    #             job_id = job_state.get('id')
    #             status_url = job_state.get('statusUrl')
    #             print(f"Resuming with existing job ID: {job_id}")
    #     except (FileNotFoundError, json.JSONDecodeError):
    #         print("Could not load job state file. Starting a new job.")
    #         job_id = None
    #         status_url = None

    if not job_id:
        # API endpoint for submitting batch jobs
        submit_url = 'https://async.scraperapi.com/batchjobs'
        api_key = 'e040fc494447cdd06abfa70304bf211f'

        # Data Payload for submitting the job
        submit_payload = {
            'apiKey': api_key,
            'urls': url_list,
            'apiParams': {
                'render': 'true', # Equivalent to x-sapi-render
                'retry_404': 'true', # Equivalent to x-sapi-retry_404
                # 'instruction_set': '[{"type": "wait", "value": 10}]' # Equivalent to x-sapi-instruction_set
            }
        }

        # Send the POST request to start the batch job
        print("Submitting batch job to ScraperAPI...")
        try:
            response = requests.post(submit_url, json=submit_payload)
            print(response.text)  # Print the response for debugging
            response.raise_for_status()
            job_details = response.json()

            # Handle case where API returns a list of jobs instead of a single object
            if isinstance(job_details, list):
                if not job_details:
                    print("Failed to get job details: ScraperAPI returned an empty list.")
                    return
                # Assuming we're interested in the first job of the batch
                job_details = job_details[0]

            job_id = job_details.get('id')
            status_url = job_details.get('statusUrl')

            if not job_id or not status_url:
                print("Failed to get job ID or status URL from ScraperAPI.")
                print(response.text)
                return

            # Save job state
            with open(job_state_filename, 'w') as f:
                json.dump(job_details, f)

            print(f"Job submitted successfully. Job ID: {job_id}")

        except requests.exceptions.RequestException as e:
            print(f"Error submitting job to ScraperAPI: {e}")
            return
        except json.JSONDecodeError:
            print("Error decoding JSON response from ScraperAPI on job submission.")
            print(response.text)
            return

    # Poll for job completion
    print("Waiting for job to complete...")
    while True:
        try:
            status_response = requests.get(status_url)
            status_response.raise_for_status()
            status_data = status_response.json()

            if status_data.get('status') == 'finished':
                print("Job finished.")
                break
            elif status_data.get('status') == 'failed':
                print("Job failed.")
                print(status_data)
                return
            else:
                print(f"Job status: {status_data.get('status')}. Checking again in 30 seconds...")
                time.sleep(30)

        except requests.exceptions.RequestException as e:
            print(f"Error checking job status: {e}")
            time.sleep(30) # Wait before retrying
        except json.JSONDecodeError:
            print("Error decoding JSON response from ScraperAPI when checking status.")
            time.sleep(30)

    # Retrieve results
    print("Retrieving scraped data...")
    page = 1
    while True:
        try:
            # The results are paginated, so we retrieve them page by page
            retrieve_url = f"https://async.scraperapi.com/batchjobs/{job_id}/results?page={page}"
            results_response = requests.get(retrieve_url)
            results_response.raise_for_status()
            results = results_response.json()

            if not results: # No more results
                break

            new_results_found = False
            for result in results:
                url = result.get('url')
                html_text = result.get('body')

                if url and url in results_data: # Skip if already processed in a previous run
                    continue

                new_results_found = True
                if url and html_text:
                    # Find the longest line
                    lines = html_text.split('\n')
                    longest_line = max(lines, key=len, default='')

                    # Filter the longest line
                    filtered_data = extract_klook_data(longest_line)

                    if filtered_data:
                        try:
                            # The extracted data is a string, but it's formatted like a JSON object.
                            # We can parse it to clean it up and store it as a proper JSON object.
                            results_data[url] = json.loads(filtered_data)
                        except json.JSONDecodeError:
                            # If it's not a valid JSON, store it as a raw string
                            results_data[url] = filtered_data
                    else:
                        results_data[url] = None # No data could be extracted
                else:
                    results_data[url] = "Failed to scrape or empty body"

            # --- Incremental Save ---
            if new_results_found:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(results_data, f, indent=4, ensure_ascii=False)
                print(f"Processed page {page} of results. Progress saved to '{output_filename}'.")
            else:
                print(f"Page {page} contained no new data. Moving on.")

            page += 1
            time.sleep(1) # Be nice to the API

        except requests.exceptions.RequestException as e:
            print(f"Error retrieving results: {e}")
            break
        except json.JSONDecodeError:
            print("Error decoding JSON from results.")
            break

    # --- Final Cleanup ---
    # Final save, just in case
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=4, ensure_ascii=False)

    # Clean up the job state file
    if os.path.exists(job_state_filename):
        os.remove(job_state_filename)

    print(f"\nScraping and processing complete. Data saved to '{output_filename}'")

if __name__ == '__main__':
    main()

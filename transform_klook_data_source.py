import json

def transform_data(input_filename="klook_activity_data.json", output_filename="transformed_klook_data.json"):
    """
    Reads Klook activity data from a JSON file, transforms it by adding new source fields
    based on existing data, and writes the result to a new JSON file.
    """
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            activities = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{input_filename}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file '{input_filename}' is not a valid JSON file.")
        return

    transformed_activities = []
    for activity in activities:
        # Create a new dictionary to avoid modifying the original list in memory
        new_activity = activity.copy()

        # Map fields as per the requirements, using .get() to handle missing keys gracefully
        new_activity['source_url'] = activity.get('klook_url')
        new_activity['source_name'] = activity.get('klook_title')
        
        location = activity.get('klook_location')
        new_activity['source_address'] = location.get('address') if isinstance(location, dict) else None
        
        price_info = activity.get('klook_price')
        if isinstance(price_info, dict) and 'sellingPrice' in price_info:
            selling_price = price_info.get('sellingPrice')
            if isinstance(selling_price, (int, float)):
                rounded_price = int(round(selling_price / 10) * 10)
                new_activity['source_pricePoint'] = f"${rounded_price}"
            else:
                new_activity['source_pricePoint'] = None
        else:
            new_activity['source_pricePoint'] = None
        new_activity['source_savedCount'] = activity.get('klook_noPastParticipants')
        
        review = activity.get('klook_review')
        new_activity['source_rating'] = review.get('score') if isinstance(review, dict) else None
        
        new_activity['source_introduction'] = activity.get('klook_summary')
        new_activity['source_photoUrls'] = [url for url in activity.get('klook_images', []) if isinstance(url, str) and url.startswith('http')]
        
        tags = activity.get('klook_tags')
        new_activity['source_Categories'] = ','.join(tags) if isinstance(tags, list) else None
        
        transformed_activities.append(new_activity)

    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(transformed_activities, f, indent=4, ensure_ascii=False)

    print(f"Transformation complete. Data saved to '{output_filename}'.")

if __name__ == '__main__':
    transform_data()
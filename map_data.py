import json

def map_activity_data(source_file, output_file):
    """
    Maps data from the source JSON file to a new format and saves it to an output file.
    """
    try:
        with open(source_file, 'r') as f:
            source_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{source_file}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: The file '{source_file}' is not a valid JSON file.")
        return

    mapped_data = []
    for item in source_data:
        # Skip empty objects
        if not item:
            continue

        tags = [
            breadcrumb.get("name")
            for breadcrumb in item.get("breadcrumbs", [])
            if breadcrumb.get("name") and breadcrumb.get("name") not in ["Klook Travel", "Hong Kong"]
        ]
        exchange_rate = 7.85
        price_info = item.get("price", {})

        try:
            market_price_usd = float(price_info.get("marketPrice", 0))
        except (ValueError, TypeError):
            market_price_usd = 0.0

        try:
            selling_price_usd = float(price_info.get("sellingPrice", 0))
        except (ValueError, TypeError):
            selling_price_usd = 0.0

        market_price_hkd = market_price_usd * exchange_rate
        selling_price_hkd = selling_price_usd * exchange_rate

        mapped_item = {
            "klook_id": item.get("id"),
            "klook_title": item.get("title", ""),
            "klook_url": item.get("url", ""),
            "klook_description": item.get("description", ""),
            "klook_summary": item.get("summary", ""),
            "klook_highlights": item.get("highlights", []),
            "klook_price": {
            "marketPrice": round(market_price_hkd, 2),
            "sellingPrice": round(selling_price_hkd, 2),
            "currency": "HKD"
            },
            "klook_location": {
            "address": item.get("location", {}).get("address", ""),
            "coordinates": item.get("location", {}).get("coordinates", ""),
            },
            "klook_review": {
            "count": item.get("review", {}).get("count", 0),
            "score": item.get("review", {}).get("score", 0.0),
            "description": item.get("review", {}).get("description", "")
            },
            "klook_noPastParticipants": item.get("noPastParticipants", ""),
            "klook_images": [img.get("url") for img in item.get("images", []) if isinstance(img, dict) and img.get("url")],
            "klook_tags": tags
        }
        mapped_data.append(mapped_item)

    try:
        with open(output_file, 'w') as f:
            json.dump(mapped_data, f, indent=4)
        print(f"Successfully mapped data and saved to '{output_file}'.")
        print(f"Total items processed: {len(mapped_data)}")
    except IOError:
        print(f"Error: Could not write to file '{output_file}'.")

if __name__ == "__main__":
    map_activity_data('structured_activity_data.json', 'klook_activity_data.json')

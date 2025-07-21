import json
import itertools
from thefuzz import fuzz

# --- Configuration ---
INPUT_FILE = 'cityline/enriched_cityline_data.json'
TOP_N = 10

def load_activities(filename):
    """Loads activities from a JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filename}.")
        return []

def calculate_similarity(activities):
    """Calculates similarity scores for all pairs of activities."""
    if not activities or len(activities) < 2:
        return []

    pairs = []
    # Use itertools.combinations to get all unique pairs
    for activity1, activity2 in itertools.combinations(activities, 2):
        name1 = activity1.get('source_name')
        name2 = activity2.get('source_name')

        if name1 and name2:
            # Using token_set_ratio is good for phrases with different word order
            score = fuzz.token_set_ratio(name1, name2)
            pairs.append(((name1, name2), score))
    
    return pairs

def main():
    """Main function to run the similarity check."""
    activities = load_activities(INPUT_FILE)
    if not activities:
        return

    similarity_pairs = calculate_similarity(activities)
    
    # Sort the pairs by score in descending order
    sorted_pairs = sorted(similarity_pairs, key=lambda x: x[1], reverse=True)
    
    print(f"Top {TOP_N} most similar activity pairs based on 'source_name':\n")
    
    for i, ((name1, name2), score) in enumerate(sorted_pairs[:TOP_N]):
        print(f"{i+1}. Score: {score}")
        print(f"   - Activity 1: {name1}")
        print(f"   - Activity 2: {name2}\n")

if __name__ == "__main__":
    main()

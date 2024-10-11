import re
from rapidfuzz import fuzz, process

def search_and_check_all_loc(locations, user_prompt):
    threshold = 70  # Define your threshold for fuzzy matching

    # Convert found locations to lowercase for case-insensitive comparison
    found_locations_lower = [loc.lower() for loc in locations]

    # Split the user prompt into words and convert to lowercase
    words_in_prompt = [word.lower() for word in user_prompt.split()]

    # Keep track of matches to clean from the user prompt
    matches_to_remove = []

    # Use fuzzy matching to find the best match for the found locations
    for loc in found_locations_lower:
        # Fuzzy match for single-word or multi-word locations
        match, score, _ = process.extractOne(
            loc, words_in_prompt, scorer=fuzz.token_sort_ratio
        )
        if score >= threshold:
            matches_to_remove.append(loc)
            print(f"Match: {loc} with score: {score}")

    # Clean the user prompt based on found matches
    cleaned_prompt = user_prompt
    for match in matches_to_remove:
        # Remove matched terms from the cleaned_prompt,
        # using case-insensitive matching
        cleaned_prompt = re.sub(
            r"\b" + re.escape(match) + r"\b[,\s!?.]*",
            "",
            cleaned_prompt,
            flags=re.IGNORECASE,
        )

    # Remove "and" if it's left with dangling commas or spaces
    cleaned_prompt = re.sub(
        r"\band\b[,\s]*", "", cleaned_prompt, flags=re.IGNORECASE
    )

    # Handle leftover commas, spaces, or "and"
    cleaned_prompt = re.sub(
        r"\s*,\s*", ", ", cleaned_prompt
    )  # Ensure single comma with a space after it
    cleaned_prompt = re.sub(
        r",\s*$", "", cleaned_prompt
    )  # Remove trailing commas
    cleaned_prompt = re.sub(r"\s+", " ", cleaned_prompt)  # Remove extra spaces
    cleaned_prompt = cleaned_prompt.strip()  # Remove leading/trailing spaces

    print("Cleaned Prompt:", cleaned_prompt)

    # Remove matched locations from the original locations list
    for match in matches_to_remove:
        if match.lower() in found_locations_lower:
            found_locations_lower.remove(match.lower())

    print("Remaining Locations:", found_locations_lower)

# Test with provided locations and prompt
locations = ['hamburg', 'rome', 'london']
user_prompt = "Compare the temperature in Rome, Hamburg and London?"

search_and_check_all_loc(locations, user_prompt)




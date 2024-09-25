import re

def clean_prompt(user_prompt, locations):
    # Convert found locations to lowercase for case-insensitive comparison
    found_locations_lower = [loc.lower() for loc in locations]

    # Use regular expressions to remove the locations, considering punctuation and case
    cleaned_prompt = user_prompt
    for loc in found_locations_lower:
        # Create a regex pattern that matches the location, ignoring case and considering punctuation and spaces
        cleaned_prompt = re.sub(r'\b' + re.escape(loc) + r'\b[,\s]*', '', cleaned_prompt, flags=re.IGNORECASE)

    # Remove "and" if it's left with dangling commas or spaces
    cleaned_prompt = re.sub(r'\band\b[,\s]*', '', cleaned_prompt, flags=re.IGNORECASE)

    # Clean up any remaining punctuation issues
    cleaned_prompt = re.sub(r'\s*,\s*', ', ', cleaned_prompt)  # Ensure single comma with a space after it
    cleaned_prompt = re.sub(r',\s*$', '', cleaned_prompt)      # Remove trailing comma
    cleaned_prompt = re.sub(r'\s+', ' ', cleaned_prompt)       # Remove extra spaces
    cleaned_prompt = cleaned_prompt.strip()                    # Remove leading/trailing spaces

    return cleaned_prompt

# Example usage
user_prompt = "Compare the temperature in Rome, Hamburg and London"
locations = ['hamburg', 'rome']

cleaned_prompt = clean_prompt(user_prompt, locations)
print(cleaned_prompt)
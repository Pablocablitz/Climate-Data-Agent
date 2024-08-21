import yaml 
import json 
from loguru import logger
import numpy as np


# TODO:
# A function to clean up the output from LLM and ensure it has consistent format (e.g. always a string that says None)

class Utilities():
    
    @staticmethod
    def load_config_file(file_path: str) -> dict:
        """
        Load YAML file.

        Args:
            file_path (str): Path to the YAML file.

        Returns:
            dict: Dictionary containing configuration information.
        """
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config

    @staticmethod
    def cleaned_dict_output(response: str) -> dict:
        """
        Cleans a JSON string by removing any content before the first `{` and after the last `}`.

        Args:
        response (str): The raw JSON response string.

        Returns:
        dict: A dictionary parsed from the cleaned JSON string.
        """
        # Find the first '{' and last '}'
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx == -1 or end_idx == -1:
            logger.error("No JSON object found in the response.")
            return None
        
        # Extract the JSON string
        json_str = response[start_idx:end_idx + 1]
        
        # Replace single quotes with double quotes for valid JSON
        json_str = json_str.replace("'", '"')
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return None
        
        
    @staticmethod
    def valueisvalid(value):
        valueisvalid = True
        if (value == "None" or value == None or not value):
            valueisvalid = False        
        return valueisvalid
    
    @staticmethod
    def significant_round(x, p):
        x_positive = np.where(np.isfinite(x) & (x != 0), np.abs(x), 10**(p-1))
        mags = 10 ** (p - 1 - np.floor(np.log10(x_positive)))
        return np.round(x * mags) / mags
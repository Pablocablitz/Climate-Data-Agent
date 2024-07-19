from cda_classes.chatbot import Chatbot
import yaml
import json
from cda_classes.prompt_manager import PromptManager

class SimpleQueryTester():
    def __init__(self):
        self.chatbot = Chatbot()
        self.tests = self.__load_tests()

    def __load_tests(self):
        # Is this correct??
        return yaml.load_all("tests.yaml")

    def run_tests(self):
        pass
    
    def key_tester(self):
        # Define example dictionaries
        timeframe_dict = {
            "time_intervals": ["2024-01-01 to 2024-01-31"]
        }

        product_dict = {
            "climate_data": None
        }

        visualization_dict = {
            "visualization_type": ["static_plot"]
        }

        analysis_dict = {
            "analysis_type": "Basic_Analysis"
        }

        multiple_products_dict = {
            "climate_data": ["Temperature", "Wind"]
        }
               
        # Collect dictionaries in a parent dictionary
        parent_dict = {
            "timeframe_agent": timeframe_dict,
            "product_agent": product_dict,
            "visualisation_agent": visualization_dict,
            "analysis_agent": analysis_dict,
            "multiple_products_agent": multiple_products_dict
        }
        
        # Iterate over each sub-dictionary and print the values
        for agent_name, sub_dict in parent_dict.items():
            print(f"Agent: {agent_name}")
            single_key = next(iter(sub_dict))
            print(f"Key: {single_key}")
            print(f"Value: {sub_dict[single_key]}\n")
            

from chatbot import Chatbot
import yaml

class EOChatbotTester():
    def __init__(self):
        self.chatbot = chatbot
        self.tests = self.__load_tests()

    def __load_tests(self):
        # Is this correct??
        return yaml.load_all("tests.yaml")

    def run_tests(self):
        pass
    
    def key_tester(self):
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
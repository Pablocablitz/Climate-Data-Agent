from llm_processor import LargeLanguageModelProcessor
from prompt_manager import PromptManager
from data_handler import DataHandler




class Chatbot():
    def __init(self):
        self.llama3 = LargeLanguageModelProcessor()
        self.prompt_manager = PromptManager()

    def display_string_to_user(response):
        #Something something streamlit
        pass

    def extract_information(self, user_prompt):
        # Step 1 - get location
        location = self.prompt_manager.generate_response("location_agent", user_prompt)

        # Step 2 - get timeframe
        timeframe = self.prompt_manager.generate_response("timeframe_agent", user_prompt)


class EORequest():
    def __init(self):
        self.request_type = None
        ## and more stuff...initialize as None I guess

    def check_validity_of_request(self):
        errors = []

        if (self.product_type == None):
            errors.append("Product type is missing\r\n")

        return errors
    
    def process_request():
        pass
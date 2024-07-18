from cda_classes.llm_processor import LargeLanguageModelProcessor
from cda_classes.prompt_manager import PromptManager
from data_handler.data_handler import DataHandler
from cda_classes.eorequest import EORequest
import json

class Chatbot():
    def __init__(self):
        self.llama3 = LargeLanguageModelProcessor()
        self.prompt_manager = PromptManager(self.llama3)

        # Can then append current requests to self.request when all requests have been processed...
        # May want to move this history functionality into a separate file (some type of logging package/module)
        # Or do it in the main, since only the main knows when a request is completed
        self.requests = []
        self.request = EORequest()

    def display_string_to_user(response):
        #Something something streamlit
        pass
    
    def check_context(self, user_prompt):
        pass

    def extract_information(self, user_prompt):
        # Initialize the dictionary to store responses
        # Step 1 - get location
        
        self.request.location = self.prompt_manager.retrieve_information("location_agent", user_prompt)

        # Step 2 - get time interval
        self.request.timeframe = self.prompt_manager.retrieve_information("timeframe_agent", user_prompt)

        # Step 3 - get product type
        self.request.product = self.prompt_manager.retrieve_information("product_agent", user_prompt)
        
        # Step 4 - get specific product name
        self.prompt_manager.specific_product_list = self.request.construct_product_agent_instruction()
        self.request.specific_product = self.prompt_manager.retrieve_information("specific_product_agent", user_prompt)

        # Step 5 - get analysis type
        self.request.analysis = self.prompt_manager.retrieve_information("analysis_agent", user_prompt)

        # Step 6 - get visualisation type
        self.request.visualisation = self.prompt_manager.retrieve_information("visualisation_agent", user_prompt)        
        
        self.requests.append(self.request)

    def process_request(self, user_prompt): 
        self.extract_information(user_prompt)
        print(self.request.check_validity_of_request())
        # data download, data processing, analysis...

        
        if (self.request.request_valid):
            pass    
        else:
            print("this is a dummy for a future callback")
            
        

    def output_results(self):
        pass



from llm_processor import LargeLanguageModelProcessor
from prompt_manager import PromptManager
from data_handler import DataHandler
from product_handler import ProductHandler
from utils import Utilities
import googlemaps



class Chatbot():
    def __init(self):
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
        # data download, data processing, analysis...
        self.request.process_request(self.requests)
        
        if (self.request.request_complete):
            
        else:
            print("this is a dummy for a future callback")
            
        

    def output_results(self):
        pass


class EORequest():
    def __init__(self):
        self.utils = Utilities()
        self.request_type = None
        self.location = None
        self.timeframe = None
        self.product = None
        self.specific_product = None
        self.analysis = None
        self.visualisation = None
        self.request_complete = False
        self.__load_variables()
        ## and more stuff...initialize as None I guess

    def check_validity_of_request(self, information_dict):
        errors = []
        for value in information_dict.items():
            if (value == None):
                errors.append(f"{value} is missing\r\n")

        return errors
    

    def process_request(self, requests):
        try:# if error occurs callback message to the user 
            errors = self.check_validity_of_request(requests)
            if errors:
                raise Exception("Missing_information")
            else:
                self.request_complete = True
            # processing of all the information
            
        except:
            print('An exception occurred in EORequest process_request')

    def construct_product_agent_instruction(self):
        product_list = [product['name'] for product in self.__variables.get(self.product, [])]
        instruction_format = f"'{self.product}':\n- {product_list}"
        return instruction_format
    
    def __load_variables(self):
        self.__variables = self.utils.load_config_file("variables.yaml") 
        
    def get_coordinates_from_location(self, api_key: str, min_size: float = 10) -> dict:
        """Get a bounding box for a location using Google Maps Geocoding API with a minimum size."""
        gmaps = googlemaps.Client(key=api_key)
        
        # Get place details
        geocode_result = gmaps.geocode(self.location)
        
        if geocode_result:
            viewport = geocode_result[0]['geometry']['viewport']
            original_bounding_box = {
                "north": viewport['northeast']['lat'],
                "south": viewport['southwest']['lat'],
                "east": viewport['northeast']['lng'],
                "west": viewport['southwest']['lng']
            }
            
            # Calculate the initial size of the bounding box
            north = original_bounding_box["north"]
            south = original_bounding_box["south"]
            east = original_bounding_box["east"]
            west = original_bounding_box["west"]

            lat_diff = north - south
            lng_diff = east - west
            
            # Ensure the bounding box has a minimum size
            if lat_diff < min_size:
                mid_lat = (north + south) / 2
                north = mid_lat + (min_size / 2)
                south = mid_lat - (min_size / 2)

            if lng_diff < min_size:
                mid_lng = (east + west) / 2
                east = mid_lng + (min_size / 2)
                west = mid_lng - (min_size / 2)
                
            adjusted_bounding_box = {"north": north, "west": west, "south": south, "east": east}


            return {
                "original_bounding_box": original_bounding_box,
                "adjusted_bounding_box": adjusted_bounding_box
            }
        else:
            return None
        
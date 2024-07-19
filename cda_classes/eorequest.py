from utils.utils import Utilities
import googlemaps
from collections.abc import Iterable


class EORequest():
    def __init__(self):
        self.request_type = None
        self.location = None
        self.timeframe = None
        self.product = None
        self.specific_product = None
        self.analysis = None
        self.visualisation = None
        self.request_valid = False
        self.variables = None
        self.load_variables()
        ## and more stuff...initialize as None I guess

    def check_validity_of_request(self):
        errors = []
        
        self.request_valid = True
        # randomobj = EORequest()
        # print(vars(randomobj))
        properties = vars(self)
            # [attr for attr in dir(EORequest) if 
            #  not callable(getattr(EORequest, attr)) 
            #  and not attr.startswith("__")]
        print(properties)
        self.main_properties = {key: value for key, value in properties.items() if not key.startswith("_")}
        print(self.main_properties)
        for key, value in self.main_properties.items():
            if isinstance(value, Iterable) and not isinstance(value, str):
                for subvalue in value:
                    if not Utilities.valueisvalid(subvalue):
                        self.request_valid = False
                        print("checking validity of property: " + str(subvalue))
                        errors.append(f"{key} is missing\r\n")
                        break  # Exit the loop after finding an invalid subvalue
            else:
                if not Utilities.valueisvalid(value):
                    self.request_valid = False
                    print("checking validity of property: " + str(value))
                    errors.append(f"{key} is missing\r\n")

        return errors
    

    def process_request(self, requests):
       pass

    def construct_product_agent_instruction(self):
        product_list = [product['name'] for product in self.variables.get(self.product[0], [])]
        print(product_list)
        instruction_format = f"'{self.product[0]}':\n- {product_list}"
        return instruction_format
    
    def load_variables(self):
        self.variables = Utilities.load_config_file("yaml/variables.yaml") 
        
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

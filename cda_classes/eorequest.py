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
        ## and more stuff...initialize as None I guess

    def check_validity_of_request(self):
        self.errors = []
        
        self.request_valid = True

        properties = vars(self)

        self.main_properties = {key: value for key, value in properties.items() if not key.startswith("_")}
        
        for key, value in self.main_properties.items():
            if isinstance(value, Iterable) and not isinstance(value, str):
                for subvalue in value:
                    if not Utilities.valueisvalid(subvalue):
                        self.request_valid = False
                        print("checking validity of property: " + str(subvalue))
                        self.errors.append(f"{key}")

                        break  # Exit the loop after finding an invalid subvalue
            else:
                if not Utilities.valueisvalid(value):
                    self.request_valid = False
                    print("checking validity of property: " + str(value))
                    self.errors.append(f"{key}")

        print(self.errors)




    def process_request(self, requests):
       pass

    def construct_product_agent_instruction(self):
        self.load_variables()
        product_list = [product['name'] for product in self.variables.get(self.product[0], [])]
        print(product_list)
        instruction_format = f"'{self.product[0]}':\n- {product_list}"
        return instruction_format
    
    def load_variables(self):
        self.variables = Utilities.load_config_file("yaml/variables.yaml") 
        


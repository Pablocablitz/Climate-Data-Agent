from utils.utils import Utilities
from loguru import logger
from collections.abc import Iterable
import streamlit as st


class EORequest():
    def __init__(self):
        self.request_type = None
        self.request_location = None
        self.request_timeframe = None
        self.request_product = None
        self.request_specific_product = None
        self.request_analysis = None
        self.request_visualisation = None
        self.request_valid = False
        self.variables = None

        self.variable = None
        self.variable_units = None
        self.variable_cmap = None
        self.variable_short_name = None

        self.data = None
        self._instance_attributes = []
        self.errors = []

    def __check_validity_of_request(self):
        self.errors = []
        
        self.request_valid = True

        # Gets all the variables of EORequest
        properties = vars(self)
        # Identify only instance attributes from all EORequest variables
        self._instance_attributes = {key: value for key, value in properties.items() if (not key.startswith("_") and key.startswith("request_"))}
        print(self._instance_attributes)
        # Iterate through them all. If iterator, get subvalue. Otherwise check directly
        for key, value in self._instance_attributes.items():
            if isinstance(value, Iterable) and not isinstance(value, str):
                for subvalue in value:
                    if not Utilities.valueisvalid(subvalue):
                        self.request_valid = False
                        logger.info("checking validity of property: " + str(subvalue))
                        self.errors.append(f"{key}")
            else:
                if not Utilities.valueisvalid(value):
                    self.request_valid = False
                    logger.info("checking validity of property: " + str(value))
                    self.errors.append(f"{key}")
                
    
    def process_request(self):
        self.__check_validity_of_request()
        if not self.errors:
            for product in self.load_variables()[self.request_product[0]]:
                if product["name"] == self.request_specific_product[0]:
                    self.variable = product["variable_name"]
                    self.variable_units = product["units"]
                    self.variable_cmap = product["cmap"]
                    self.variable_short_name = product["short_name"]


    def construct_product_agent_instruction(self):
        product_list = [product['name'] for product in self.load_variables()[self.request_product[0]]]
        instruction_format = f"'{self.request_product[0]}':\n- {product_list}"
        return instruction_format
    
    def load_variables(self):
        return Utilities.load_config_file("yaml/variables.yaml") 

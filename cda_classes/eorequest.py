from utils.utils import Utilities
from loguru import logger
from collections.abc import Iterable
import streamlit as st
import numpy as np


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
                    self.vmin = product["vmin"]
                    self.vmax = product["vmax"]


    def construct_product_agent_instruction(self):
        product_list = [product['name'] for product in self.load_variables()[self.request_product[0]]]
        instruction_format = f"'{self.request_product[0]}':\n- {product_list}"
        return instruction_format
    
    def load_variables(self):
        return Utilities.load_config_file("yaml/variables.yaml") 
    
    def store_and_process_data(self, data):
        self.data = data
        variable_names = list(self.data.data_vars)
        
        match(variable_names[0]):
            case "v10":
                self._process_windspeed()
                
            case "u10":
                self._process_windspeed()
                
            case "e":
                self.data["e"] *= -1000  #convert from kelvin to celsius 
                               
            case "t2m":
                self.data["t2m"] -= 273.15  #convert from kelvin to celsius

            case "skt":
                self.data["skt"] -= 273.15  #convert from kelvin to celsius

            case "tp":
                self.data["tp"] *= 1000 #convert m to mm in precipitation data

            case _:
                message = "Unexpected type of variable name provided! Received:" + variable_names[0]
                logger.error(message)
                
    def _process_windspeed(self):
        """
        calculate wind speed on component vectors u and v
        """
        w10 = np.sqrt(self.data['u10']**2 + self.data['v10']**2)
        
        # Add 'w10' to the dataset
        self.data['w10'] = w10
        
        # Remove 'v10' and 'u10' from the dataset
        self.data = self.data.drop_vars(['v10', 'u10'])
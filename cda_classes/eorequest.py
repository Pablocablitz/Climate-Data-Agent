from utils.utils import Utilities
from loguru import logger
import googlemaps
from collections.abc import Iterable
import streamlit as st


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
        self.data = "ToBeFilledAfterDownload"

    def check_validity_of_request(self):
        self.errors = []
        
        self.request_valid = True

        # Gets all the variables of EORequest
        properties = vars(self)
        # Identify only instance attributes from all EORequest variables
        self.instance_attributes = {key: value for key, value in properties.items() if not key.startswith("_")}
        # Iterate through them all. If iterator, get subvalue. Otherwise check directly
        for key, value in self.instance_attributes.items():
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

    # def check_history(self):
    #     st.session_state.messages.append({"role": "user", "validity": self.request_valid})
    #     messages = st.session_state.messages
    #     if len(messages) >= 2 and messages["validity"][-2]:
    #         with st.chat_message(messages["validity"][-2]):
    #             if messages.get("validity"):
    #                 print(message)
                

    
    def process_request(self, requests):
       pass

    def construct_product_agent_instruction(self):
        self.load_variables()
        product_list = [product['name'] for product in self.variables.get(self.product[0], [])]
        instruction_format = f"'{self.product[0]}':\n- {product_list}"
        return instruction_format
    
    def load_variables(self):
        self.variables = Utilities.load_config_file("yaml/variables.yaml") 

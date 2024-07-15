from loguru import logger
import transformers
import torch
from typing import Dict, List, Any
from utils import clean_json_response

class LLM:
    def __init__(self, llm_config: dict):
        """
        Initialize the LLM class.
        """
        self.llm = llm_config["model_name"]
        self.system_prompts = llm_config["system_prompts"]
        self.pipeline = transformers.pipeline(
            "text-generation",
            model=self.llm,
            device=0 if torch.cuda.is_available() else -1,  # Use GPU if available
            model_kwargs={"torch_dtype": torch.float16 if torch.cuda.is_available() else torch.bfloat16},
        )
    def get_user_message(self, user_message: str):
        self.prompt = user_message
        
    def agent(self, ag, descriptions_text = None, category = None , product_list = None):
        """
        get Response on your input prompt and system prompt
        """
        system_prompt = ag.format(prompt = self.prompt, descriptions_text = descriptions_text,  category = category, product_list = product_list)
        messages = [
            {"role": "system", "content": system_prompt},
        
        ]
        # Generate the response
        outputs = self.pipeline(
        messages,
        max_new_tokens = 4000,
        do_sample = True,
        temperature = 0.5,
        top_p=0.95,
        )

        # Extract the generated text
        response = outputs[0]["generated_text"][-1]

        return response
    
    def set_agent(self, system_prompt: str, descriptions_text = None, product_list = None, category = None):
        """
        Detect the location information using the LLM agent.
        
        Returns:
            dict: The response content from the LLM agent.
        """
        system_prompt = self.system_prompts[system_prompt]
      
        try:
          response = self.agent(system_prompt, descriptions_text = descriptions_text, category = category, product_list = product_list)
          text_response = response['content']
          return text_response
        except Exception as e:
            logger.error(f"Issue in the LLM location configuration: {e}")
            return {}
    
    def get_details_from_short_name(self, data, short_name):
        for category, items in data.items():
            for item in items:
                if item.get('short_name') == short_name:
                    self.product = item.get('name')
                    self.units = item.get('units')
                    self.category = category
                    return self.product, self.units, self.category
        return None, None, None
    
    def data_processing(self, data, variables_config, variable):
        """
        Process the data to remove any missing values and convert temperature to Celsius.
        
        Parameters:
            data (xarray.Dataset): The data to be processed.
            category (str): The category of the data ("Temperature", "Precipitation", "Wind").
            variable_names (list): List of variable names to be processed.
        
        Returns:
            xarray.Dataset: The processed data.
        """    
    
        name, units, category = self.get_details_from_short_name(variables_config, variable)
        # print(name, units, category)
        if category == "Temperature":
                # Convert temperature from Kelvin to Celsius
                data[variable] = data[variable] - 273.15
        
        elif category == "Precipitation":
                # Convert precipitation from meters to millimeters
                data[variable] = data[variable] * 1000
        
        return data, category, units, name
    
    def get_product_information(self) -> Dict[str, Any]:
        try:
            agent_name = "Detect_product_type"
            product_info = self.set_agent(agent_name)
            return clean_json_response(product_info)
        except Exception as e:
            logger.error(f"Error getting product information with agent {agent_name}: {e}")
            return {}
    
    def get_specific_product_information(self, product_list: List[str], category: str) -> Dict[str, Any]:
        try:
            agent_name = "Determine_specific_product"
            specific_product_info = self.set_agent(agent_name, product_list=product_list, category=category)
            return clean_json_response(specific_product_info)
        except Exception as e:
            logger.error(f"Error getting specific product information for category {category} with agent {agent_name}: {e}")
            return {}
    
    def get_geo_information(self) -> Dict[str, Any]:
        try:
            agent_name = "detect_location_years"
            geo_info = self.set_agent(agent_name)
            return clean_json_response(geo_info)
        except Exception as e:
            logger.error(f"Error getting geo information with agent {agent_name}: {e}")
            return {}
    
    def get_review_request(self, variable_names: List[str], geo_info: Dict[str, Any], product_info: Dict[str, Any]) -> Dict[str, Any]:
        
        status_response = {
            "status": "error",
            "data": {}
            }
    
        try:
            description, missing_key_message = self.generate_product_review_description(variable_names, product_info, geo_info)
            
            if missing_key_message:
                agent_name = "Callback_agent"
                information_notification = self.set_agent(agent_name, descriptions_text = missing_key_message)
                logger.info("Callback_agent selected")
                status_response.update({
                "status": "information_notification",
                "data": information_notification
                })
            
            else:
                agent_name = "Review_agent"
                review_request = self.set_agent(agent_name, descriptions_text=description)
                logger.info("Review_agent selected")
                status_response.update({
                "status": "success",
                "data": review_request
                })
            
        except Exception as e:
            logger.error(f"Error getting review request with agent {agent_name}: {e}")
            status_response.update({
            "error_message": str(e)
            })
                
            return status_response
    
    def generate_product_review_description(self, variables: List[str], product_info: Dict[str, Any], geo_info: Dict[str, Any]) -> str:
        """
        Generates a descriptive string based on the given product review data.

        Args:
        - variables (list): List of variables.
        - category (dict): Dictionary containing the main product type.
        - geo_information (dict): Dictionary containing the location, start year, and end year.

        Returns:
        - str: Descriptive string for the product review.
        """
        missing_keys = []
        
        required_keys = ['climate_data']
        for key in required_keys:
            if key not in product_info or product_info[key] in [None, "None"]:
                missing_keys.append((key))

        required_geo_keys = ['location', 'start_year', 'end_year']
        for key in required_geo_keys:
            if key not in geo_info or geo_info[key] in [None, "None"]:
                missing_keys.append((key))
        # If there are missing keys, handle them
        if missing_keys:
            missing_key_message = self.missing_info_handler(missing_keys)
            
            return "", missing_key_message # Exit the function after handling the missing info

        
        main_product_type = product_info['climate_data']
        variable_name = ', '.join(variables)
        location = geo_info['location']
        start_year = geo_info['start_year']
        end_year = geo_info['end_year']
    
        description = (
            f"I will search for the climate product for {location} covers the period from {start_year} to {end_year}. "
            f"The primary focus is on the category '{main_product_type}', specifically looking at the variable '{variable_name}'."
        )
        
        return description, ""

    def missing_info_handler(self, missing_keys: List[tuple]) -> str:
        """
        Handles missing information by calling a pseudo LLM to inform the user.

        Args:
        - missing_keys (list): List of tuples containing the missing key and the source dictionary.

        Returns:
        - str: Message to inform the user about the missing information.
        """
        # Generate a message to inform the user about all missing keys
        missing_info = [f"{key}" for key in missing_keys]
        message = "The following required information is missing: " + ", ".join(missing_info) + "."
        
        # Return the message (or replace this with a call to an actual LLM function or logging)
        return message

    def climate_data_context(self, agent_name: str) -> Dict[str, Any]:
        """
        Checks if Climate context ist full filled
        
        Args:
        user_message
        
        Returns:
        Context: "True" or "False" 
        """
        try:
            user_interest = self.set_agent(agent_name)
            return clean_json_response(user_interest)
        except Exception as e:
            logger.error(f"Error getting review request with agent {agent_name}: {e}")
            return {}
    
    def general_response(self, agent_name ):
        """
        In case no climate data is asked for it will create an general response 
        """
        try:
            qanda = self.set_agent(agent_name)
            return qanda
        except Exception as e:
            logger.error(f"Error getting review request with agent {agent_name}: {e}")
            return {}
        
    def check_same_context(self, previous_message):
        """
        
        """
        agent_name = "Similarity_detection"
        try:
            similarity = self.set_agent(agent_name, descriptions_text = previous_message)
            return  clean_json_response(similarity)
        except Exception as e:
            logger.error(f"Error getting review request with agent {agent_name}: {e}")
            return {}

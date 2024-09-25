import string

from cda_classes.llm_processor import LargeLanguageModelProcessor
from cda_classes.analysis_handler import AnalysisHandler
from cda_classes.eorequest import EORequest
from datetime import datetime
from utils.utils import Utilities
from loguru import logger

class PromptManager():
    def __init__(self, llm_handler: LargeLanguageModelProcessor):
        self.llm_handler = llm_handler
        self.__load_agents()
        self.specific_product_list = None
        self.request = None
        self.analysis_handler = AnalysisHandler()
        
    
    def retrieve_information(self, agent_type, user_prompt):
        system_prompt = self.construct_system_prompt(agent_type, user_prompt)
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Try to generate a response using the LLM handler
                information = self.llm_handler.generate_response(system_prompt)
                logger.info(f"Extracted the following information from user prompt: {information}")
                
                # Clean the extracted information
                cleaned_information = Utilities.cleaned_dict_output(information)
                
                # Extract values from the cleaned information
                dict_values = list(cleaned_information.values())
                
                # Flatten the values if necessary
                flattened_values = []
                for value in dict_values:
                    if isinstance(value, list):
                        flattened_values.extend(value)  # Add items from the list
                    else:
                        flattened_values.append(value)  # Add single value
                
                # Return the flattened values
                return flattened_values
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed with error: {e}")
                
                # If max retries are reached, log and return an error message
                if attempt + 1 == max_retries:
                    logger.error("Max retries reached. Unable to retrieve information.")
                    return {"error": "Unable to retrieve information after multiple attempts."}  # Return an error after retries

    def callback_assistant_to_user(self, agent_type, user_prompt, request: EORequest):
        self.request = request
        system_prompt = self.construct_system_prompt(agent_type, user_prompt)
        self.callback = system_prompt
        
        
    def __load_agents(self):
        self.__agents = Utilities.load_config_file("yaml/agents.yaml")

    def construct_system_prompt(self, agent_type, user_prompt):
        # Check if the attribute name exists in the config
        if agent_type not in self.__agents['attributes']:
            raise ValueError(f"Attribute '{agent_type}' not found in the configuration.")
        
        # Get the attribute details from the config
        attributes = self.__agents['attributes'][agent_type]


        # Format the general template with the attribute details
        system_prompt = self.__agents['general_template'].format(
            expertise_area  = attributes["expertise_area"],
            task_description = attributes["task_description"],
            prompt = user_prompt,
            list_of_types = attributes["list_of_types"],
            response_type = attributes["response_type"],
            guideline_1 = attributes["guideline_1"],
            guideline_2 = attributes["guideline_2"],
            guideline_3 = attributes["guideline_3"],
            guideline_4 = attributes["guideline_4"]
            )
        
        if agent_type == "specific_product_agent":
            system_prompt = system_prompt.format(specific_product_list = self.specific_product_list)
        elif agent_type == "review_agent":
            if len(self.request.request_timeframes) == 1:
                timeframes = f'{self.request.request_timeframes[0].startdate_str} to {self.request.request_timeframes[0].enddate_str}'
            else:    
                timeframes = ', '.join(f'{ts.startdate_str} to {ts.enddate_str}' for ts in self.request.request_timeframes[:-1])
            if len(self.request.request_timeframes) > 1:
                timeframes += f' and {self.request.request_timeframes[-1].startdate_str} to {self.request.request_timeframes[-1].enddate_str}'

            match(self.request.request_analysis[0]):
                case "basic_analysis":

                    analysis_type = 'Basic Analysis'

                case "comparison":
                    analysis_type = 'Comparison'

                case "predictions":
                    analysis_type = 'Prediction'
                case _:  # Fallback case to handle unexpected values
                    analysis_type = 'Unspecified Analysis'
            # Determine whether to use "period" or "periods"
            period_label = "period" if len(self.request.request_timeframes) == 1 else "periods"
            
            system_prompt = f"""
            <p style='color: white;'>
                I will search for the climate product for 
                <span style='background-color:#292C37; color:white; padding: 2px 2px; border-radius: 5px;'>{', '.join(self.request.request_locations)}</span> 
                covering the {period_label} <span style='background-color:#292C37; color:white; padding: 2px 2px; border-radius: 5px;'>{timeframes}</span>. 
                The primary focus is on the category 
                <span style='background-color:#292C37; color:white; padding: 2px 2px; border-radius: 5px;'>{self.request.request_product[0]}</span>, 
                specifically looking at the variable 
                <span style='background-color:#292C37; color:white; padding: 2px 2px; border-radius: 5px;'>{self.request.request_specific_product[0]}</span>. 
                The analysis type being displayed is a 
                <span style='background-color:#292C37; color:white; padding: 2px 2px; border-radius: 5px;'>{analysis_type}</span>.
            </p>
            """
            
        elif agent_type == "analysis_agent":
            temp_prompt = string.Template(system_prompt)
            system_prompt = temp_prompt.safe_substitute(
                {'analysis_types' : self.analysis_handler.analysis_types})
        elif agent_type == "missing_info_agent":
            formatted_string = '\n'.join(f"- {item.replace('request_', '').capitalize()}" for item in self.request)
            system_prompt = f"Thank you for providing the product details. However, some required information is missing:\n\n{formatted_string}\n\nCould you please provide the missing information so I can assist you further?"
        elif agent_type == "time_range_extraction_agent":
            now = datetime.now()
            date_str = now.strftime('%Y')
            system_prompt = system_prompt.format(current_date = date_str)

        return system_prompt
    
    # show me temperature in rome in 2012
    
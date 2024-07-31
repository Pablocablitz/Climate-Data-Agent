import yaml
import string
from utils.utils import Utilities
from loguru import logger
import jsonpickle 
from cda_classes.llm_processor import LargeLanguageModelProcessor
from cda_classes.analysis_handler import AnalysisHandler


class PromptManager():
    def __init__(self, llm_handler: LargeLanguageModelProcessor):
        self.llm_handler = llm_handler
        self.__load_agents()
        self.specific_product_list = None
        self.request = None
        self.analysis_handler = AnalysisHandler()
        pass
    
    def retrieve_information(self, agent_type, user_prompt):
        system_prompt = self.construct_system_prompt(agent_type, user_prompt)
        information = self.llm_handler.generate_response(system_prompt)
        logger.info(f"Extracted the following information from user prompt: {information}")
        cleaned_information = Utilities.cleaned_dict_output(information)
        # Responses only ever have one key value pair, so grab next key to know type of response (timeframe, location...)
        dict_key = next(iter(cleaned_information)) 
        dict_value = cleaned_information[dict_key]
        if not isinstance(dict_value, list):
            dict_value = [dict_value]
        return dict_value
    
    # creating Callback to user before pulling request or notify of missing information
    def callback_assistant_to_user(self, agent_type, user_prompt, request):
        self.request = request
        system_prompt = self.construct_system_prompt(agent_type, user_prompt)
        self.callback = self.llm_handler.generate_response(system_prompt)
        
        
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
            system_prompt = system_prompt.format(
                collected_information=(
                    f"I will search for the climate product for {self.request.location} "
                    f"covering the period {self.request.timeframe}. "
                    f"The primary focus is on the category '{self.request.product}', "
                    f"specifically looking at the variable '{self.request.specific_product}'."
                )
            )
        elif agent_type == "analysis_agent":
            temp_prompt = string.Template(system_prompt)
            system_prompt = temp_prompt.safe_substitute(
                {'analysis_types' : self.analysis_handler.analysis_types})
        elif agent_type == "missing_info_agent":
            formatted_string = '\n'.join(f"- {item}" for item in self.request)
            system_prompt = system_prompt.format(errors = f"{formatted_string}")

        return system_prompt
    
    # show me temperature in rome in 2012
    
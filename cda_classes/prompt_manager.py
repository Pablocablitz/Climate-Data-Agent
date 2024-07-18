import yaml
from utils.utils import Utilities

class PromptManager():
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler
        self.__load_agents()
        self.specific_product_list = None
        pass
    
    def retrieve_information(self, agent_type, user_prompt):
        system_prompt = self.__construct_system_prompt(agent_type, user_prompt)
        information = self.llm_handler.generate_response(system_prompt)
        cleaned_information = Utilities.cleaned_dict_output(information)
        # Responses only ever have one key value pair, so grab next key to know type of response (timeframe, location...)
        dict_key = next(iter(cleaned_information)) 
        dict_value = cleaned_information[dict_key]
        return dict_value

    def __load_agents(self):
        self.__agents = Utilities.load_config_file("yaml/agents.yaml")

    def __construct_system_prompt(self, agent_type, user_prompt):
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
        )
        
        if agent_type == "specific_product_agent":
            system_prompt = system_prompt.format(specific_product_list = self.specific_product_list)
            
        return system_prompt
    
    # show me temperature in rome in 2012
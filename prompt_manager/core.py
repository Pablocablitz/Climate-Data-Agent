import yaml

class PromptManager():
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler
        self.__load_agents()
        pass
    
    def retrieve_information(self, agent_type, user_prompt):
        system_prompt = self.__construct_system_prompt(agent_type)
        information = self.llm_handler.generate_response(system_prompt, user_prompt)
        # Responses only ever have one key value pair, so grab next key to know type of response (timeframe, location...)
        dict_key = next(iter(information)) 
        dict_value = information[dict_key]
        return dict_value

    def __load_agents(self):
        self.__agents = self.load_config_file("agents.yaml")

    def __construct_system_prompt(self, agent_type):
                # Check if the attribute name exists in the config
        if agent_type not in self.__agents['attributes']:
            raise ValueError(f"Attribute '{agent_type}' not found in the configuration.")
        
        # Get the attribute details from the config
        attribute = self.__agents['attributes'][agent_type]
        
        # Format the general template with the attribute details
        system_prompt = self.__agents['general_template'].format(
            expertise_area=attribute["expertise_area"],
            task_description=attribute["task_description"],
            list_of_types=attribute["list_of_types"],
            response_type=attribute["response_type"],
            guideline_1=attribute["guideline_1"],
            guideline_2=attribute["guideline_2"],
        )
        
        return system_prompt
    
    def load_config_file(file_path: str) -> dict:
        """
        Load YAML file.

        Args:
            file_path (str): Path to the YAML file.

        Returns:
            dict: Dictionary containing configuration information.
        """
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
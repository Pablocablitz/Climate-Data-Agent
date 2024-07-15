class PromptManager():
    def __init__(self, llm_handler):
        self.llm_handler = llm_handler
        self.__load_agents()
        pass
    
    def retrieve_information(self, agent_type, user_prompt):
        system_prompt = self.__construct_system_prompt(agent_type)

        pass

    def __load_agents(self):
        self.__agents = loadconfigfile("agents.yaml")

    def __construct_system_prompt(self, agent_type, user_prompt):
        pass
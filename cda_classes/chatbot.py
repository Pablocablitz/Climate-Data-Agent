from cda_classes.llm_processor import LargeLanguageModelProcessor
from cda_classes.prompt_manager import PromptManager
from data_handler.data_handler import DataHandler
from cda_classes.eorequest import EORequest
from cda_classes.visualisation_handler import VisualisationHandler
import streamlit as st

@st.cache_resource    
def load_llm():
    llm = LargeLanguageModelProcessor()
    return llm

class Chatbot():
    def __init__(self):
        self.llama3 = load_llm()
        self.prompt_manager = PromptManager(self.llama3)
        self.data_handler = DataHandler()
        self.vis_handler = VisualisationHandler()

        # Can then append current requests to self.request when all requests have been processed...
        # May want to move this history functionality into a separate file (some type of logging package/module)
        # Or do it in the main, since only the main knows when a request is completed
        self.request = EORequest()
        

    def display_string_to_user(response):
        #Something something streamlit
        pass
    
    def check_context(self, user_prompt):
        pass

    def extract_information(self, user_prompt):
        # Initialize the dictionary to store responses
        
        # Step 0 - check context
        self.request.request_type = self.prompt_manager.retrieve_information("request_type_agent", user_prompt)
        # Step 1 - get location
        
        self.request.location = self.prompt_manager.retrieve_information("location_agent", user_prompt)

        # Step 2 - get time interval
        self.request.timeframe = self.prompt_manager.retrieve_information("timeframe_agent", user_prompt)

        # Step 3 - get product type
        self.request.product = self.prompt_manager.retrieve_information("product_agent", user_prompt)
        
        # Step 4 - get specific product name
        self.prompt_manager.specific_product_list = self.request.construct_product_agent_instruction()
        self.request.specific_product = self.prompt_manager.retrieve_information("specific_product_agent", user_prompt)

        # Step 5 - get analysis type
        self.request.analysis = self.prompt_manager.retrieve_information("analysis_agent", user_prompt)

        # Step 6 - get visualisation type
        self.request.visualisation = self.prompt_manager.retrieve_information("visualisation_agent", user_prompt)        


     # setting message block for assistant in the case of callback to user 
     
    def callback_user(self, user_prompt):
        if (self.request.request_valid):
            self.prompt_manager.callback_assistant_to_user("review_agent", user_prompt, self.request.main_properties)
            with st.chat_message("assistant"):
                st.write(self.prompt_manager.callback)
                st.session_state.messages.append({"role": "assistant", "content": self.prompt_manager.callback})
            pass    
        else:
            with st.chat_message("assistant"):
                self.prompt_manager.callback_assistant_to_user("missing_info_agent", user_prompt, self.request.errors)
                st.write(self.prompt_manager.callback)
                st.session_state.messages.append({"role": "assistant", "content": self.prompt_manager.callback})
                st.stop()

    def process_request(self, user_prompt): 
        
        self.extract_information(user_prompt)
        if self.request.request_type == "False":
            with st.chat_message("assistant"):
                non_climate_data = "Thanks for your request. However there is no climate context. Please provide more accurate information."
                st.write(non_climate_data)
                st.session_state.messages.append({"role": "assistant", "content": non_climate_data})
                st.stop()
                
        self.request.check_validity_of_request()
        # data download, data processing, analysis...
        
        print(len(st.session_state.past_request))
        st.session_state.past_request.append({"request": self.request})
        
        print(len(st.session_state.past_request))
        if len(st.session_state.past_request)>=2:
            location = st.session_state.past_request[-2]["request"].location
            print(f"{location}, your location")
        
        self.callback_user(user_prompt)
        
        with st.spinner("Downloading Data..."):
            self.data_handler.construct_request(self.request)
            self.data_handler.download("ERA5")
        
            # self.vis_handler.visualise_data(self.data_handler)
            self.vis_handler.visualise_data(self.data_handler)
        
        with st.chat_message("assistant"):
            # st.write(response)
            if self.vis_handler.output_path:
                st.video(self.vis_handler.output_path)
        
        st.session_state.messages.append({"role": "assistant","video": self.vis_handler.output_path})

    def output_results(self):
        pass



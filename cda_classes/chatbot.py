from cda_classes.llm_processor import LargeLanguageModelProcessor
from cda_classes.prompt_manager import PromptManager
from data_handler.data_handler import DataHandler
from cda_classes.eorequest import EORequest
from cda_classes.visualisation_handler import VisualisationHandler
from cda_classes.analysis_handler import AnalysisHandler
import streamlit as st
import jsonpickle
from loguru import logger

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
        self.analysis_handler = AnalysisHandler()

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
        
        self.request.request_location = self.prompt_manager.retrieve_information("location_agent", user_prompt)

        # Step 2 - get time interval
        self.request.request_timeframe = self.prompt_manager.retrieve_information("timeframe_agent", user_prompt)

        # Step 3 - get product type
        self.request.request_product = self.prompt_manager.retrieve_information("product_agent", user_prompt)
        
        # Step 4 - get specific product name
        if self.request.request_product[0] != "None" and self.request.request_product[0] != None:
            self.prompt_manager.specific_product_list = self.request.construct_product_agent_instruction()
            self.request.request_specific_product = self.prompt_manager.retrieve_information("specific_product_agent", user_prompt)

        # Step 5 - get analysis type
        self.request.request_analysis = self.prompt_manager.retrieve_information("analysis_agent", user_prompt)

        # Step 6 - get visualisation type
        self.request.request_visualisation = self.prompt_manager.retrieve_information("visualisation_agent", user_prompt)        


     # setting message block for assistant in the case of callback to user 
     
    def callback_user(self, user_prompt):
        if (self.request.request_valid):
            self.prompt_manager.callback_assistant_to_user("review_agent", user_prompt, self.request)
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

        self.request.process_request()

        # data download, data processing, analysis...
        st.session_state.past_request.append(self.request)
        

        # check if the context is related to history or has no relation with climate at all 
        if ((len(st.session_state.past_request) >= 2) and (not st.session_state.past_request[-2].request_valid)):
            self.check_history()
        elif self.request.request_type == "False":
            self.check_climate_context()
        else:
            pass
        
        self.callback_user(user_prompt)
    
        with st.spinner("Downloading Data..."):
        
            self.data_handler.construct_request(self.request)
            self.data_handler.download("ERA5")

            self.request.data = self.data_handler.data

            # self.vis_handler.visualise_data(self.data_handler)
            self.vis_handler.visualise_data(self.data_handler)

        if (isinstance(self.request.request_analysis, str) and not ( self.request.request_analysis == None or self.request.request_analysis == "")):
            match(self.request.request_analysis):
                case "basic_analysis":
                    message = self.analysis_handler.basic_analysis(self.request)

                case "comparison":
                    message = self.analysis_handler.comparison(self.request)

                case "predictions":
                    message = self.analysis_handler.predictions(self.request)

                case "significant_event_detection":
                    message = self.analysis_handler.significant_event_detection(self.request)

                case _:
                    message = "Unexpected type of analysis provided! Received:" + self.request.analysis
                    logger.error(message)
                
            st.write(message)
            st.session_state.messages.append({"role": "assistant", "content": message})

        else:
            logger.info("No analysis type was present.")
                
        with st.chat_message("assistant"):
            # st.write(response)
            if self.vis_handler.output_path:
                st.video(self.vis_handler.output_path)
        
        st.session_state.messages.append({"role": "assistant","video": self.vis_handler.output_path})

    def output_results(self):
        pass
    
    def replace_last_entry(self):
        if st.session_state.past_request:
            st.session_state.past_request[-1] = self.past_request
    
    def check_history(self):
            # Get the second-to-last request
            self.past_request = st.session_state.past_request[-2]

            # Print the initial state of past_request and self.request
            print("Initial past_request:", self.past_request)
            print("Initial self.request:", self.request)

            # Check if the second-to-last request was invalid and has errors
            if not self.past_request.request_valid and self.past_request.errors:
                # Update the past request attributes based on the errors
                for error in self.past_request.errors:
                    # Check if the attribute exists in self.request
                    if hasattr(self.request, error):
                        # Retrieve the value from self.request
                        value = getattr(self.request, error)
                        # Set the value to past_request
                        setattr(self.past_request, error, value)
                        
                        # Print the attribute and value being set
                        print(f"Updating {error} in past_request to {value}")

                # Print the updated state of past_request
                print("Updated past_request:", self.past_request)

                # Set the current request to be the updated past request
                self.request = self.past_request

                # Print the final state of self.request
                print("Final self.request:", self.request)
                self.request.request_valid = True
                self.replace_last_entry()
            else:
                pass
        
    def check_climate_context(self):
        with st.chat_message("assistant"):
            non_climate_data = "Thanks for your request. However there is no climate context. Please provide more accurate information."
            st.write(non_climate_data)
            st.session_state.messages.append({"role": "assistant", "content": non_climate_data})
            st.stop()     

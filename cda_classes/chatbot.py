import streamlit as st
import torch
import gc
import regex as re

from loguru import logger
from cda_classes.llm_processor import LargeLanguageModelProcessor
from cda_classes.prompt_manager import PromptManager
from data_handler.data_handler import DataHandler
from cda_classes.eorequest import EORequest
from cda_classes.visualisation_handler import VisualisationHandler
from cda_classes.analysis_handler import AnalysisHandler
from datetime import datetime
from rapidfuzz import fuzz, process
from utils.utils import apply_timing_decorator


DEBUGMODE = False


@st.cache_resource    
def load_llm():        
    torch.cuda.empty_cache()
    gc.collect()
    llm = LargeLanguageModelProcessor()
    return llm

@apply_timing_decorator
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
        
        if (DEBUGMODE):
            with st.chat_message("assistant"):
                st.write("NOTE: THE DEBUGMODE IS ENABLED AND ALL REQUESTS WILL BE IGNORED. DUMMY DATA WILL BE LOADED AND DISPLAYED")
                
    def check_request(self, user_prompt):
        self.request.request_type = self.prompt_manager.retrieve_information("request_type_agent", user_prompt)

    def extract_information(self, user_prompt):
        # Initialize the dictionary to store responses
        
        # Step 0 - check context
        # self.request.request_type = self.prompt_manager.retrieve_information("request_type_agent", user_prompt)
        
        # Step 1 - get location
        self.request.request_locations = self.prompt_manager.retrieve_information("location_agent", user_prompt)
        self.request.request_locations = self.search_and_check_all_loc(self.request.request_locations, user_prompt)
        
        # Step 2 - get time interval
        time_contexts = self.prompt_manager.retrieve_information("time_context_extractor_agent", user_prompt)
        
        if any(context is None or context == 'None' for context in time_contexts):
            # If there is None or 'None' in the list, create a new list with one entry and return it
            self.request.request_timeframes = ['None']  # Replace 'default_time_entry' with your desired entry
        else:
            for time_context in time_contexts:
                self.request.process_and_store_timeframe(self.prompt_manager.retrieve_information("time_range_extraction_agent", time_context))
                
        # Step 3 - get product type
        self.request.request_product = self.prompt_manager.retrieve_information("product_agent", user_prompt)
        
        # Step 4 - get specific product name
        if self.request.request_product[0] != "None" and self.request.request_product[0] != None:
            self.prompt_manager.specific_product_list = self.request.construct_product_agent_instruction()
            self.request.request_specific_product = self.prompt_manager.retrieve_information("specific_product_agent", user_prompt)

        # Step 5 - get analysis type
        self.request.request_analysis = self.prompt_manager.retrieve_information("analysis_agent", user_prompt)
        # Step 5.1 - if one location and comparison is detected then try to find the two different time ranges
        if self.request.request_analysis[0] == 'comparison':
            self.request.multi_loc_request = True
            if len(self.request.request_locations) == 1:
                #self.request.request_timeframe = self.prompt_manager.retrieve_information("compare_timeframe_agent", user_prompt)
                self.request.multi_time_request = True
                self.request.multi_loc_request = False
        # elif self.request.request_analysis[0] == 'predictions':
        #     self.request.prediction_number = 
            
        # Step 6 - get visualisation type
        # self.request.request_visualisation = self.prompt_manager.retrieve_information("visualisation_agent", user_prompt)        
        
        self.request.post_process_request_variables()


     # setting message block for assistant in the case of callback to user 
     
    def callback_user(self, user_prompt):
        if (self.request.request_valid):
            self.prompt_manager.callback_assistant_to_user("review_agent", user_prompt, self.request)
            with st.chat_message("assistant"):
                st.markdown(self.prompt_manager.callback, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "request_info": self.prompt_manager.callback})
            pass    
        else:
            with st.chat_message("assistant"):
                self.prompt_manager.callback_assistant_to_user("missing_info_agent", user_prompt, self.request.errors)
                st.write(self.prompt_manager.callback)
                st.session_state.messages.append({"role": "assistant", "request_info": self.prompt_manager.callback})
                st.stop()

    def process_request(self, user_prompt): 
        self.request.user_prompt = user_prompt
        if (not DEBUGMODE):
            self.check_request(user_prompt)
            print(self.request.request_type[0])
            print(len(st.session_state.past_request), self.request.request_type[0])
            if ((len(st.session_state.past_request) >= 1) and (not st.session_state.past_request[-1].request_valid)):
                # new_request = self.prompt_manager.retrieve_information("new_request_agent", user_prompt)
                # if new_request[0] == 'False':
                combined_prompt = f'{user_prompt} and {st.session_state.past_request[-1].user_prompt}'
                self.extract_information(combined_prompt)
                # else:
                #     self.extract_information(user_prompt)
            elif self.request.request_type[0] == False or self.request.request_type[0] == 'False':
                if len(st.session_state.past_request) < 1:
                    self.check_climate_context()
                elif st.session_state.past_request[-1].request_valid:
                    self.check_climate_context()
            else:
                self.extract_information(user_prompt)

            

            self.request.process_request()
            
            self.analysis_compatability()
            # data download, data processing, analysis...
            st.session_state.past_request.append(self.request)
            
            # History version 0 is discontinued
            # check if the context is related to history or has no relation with climate at all 
            # if ((len(st.session_state.past_request) >= 2) and (not st.session_state.past_request[-2].request_valid)):
            #     self.check_history()
            # elif self.request.request_type == "False":
            #     self.check_climate_context()
            # else:
            #     pass
            
            self.callback_user(user_prompt)
    

    
        with st.spinner("Downloading Data..."):
        
            if DEBUGMODE:
                self.request.populate_dummy_data()
            else:
                self.request.collect_eorequests()
                
                self.data_handler.download(self.request)
                self.request.store_and_process_data()
                self.animation = self.vis_handler.visualise_data(self.request)
            
        
        analysis_type = self.request.request_analysis[0]        
        if (isinstance(analysis_type, str) and not ( analysis_type == None or analysis_type == "")):
            match(analysis_type):
                case "basic_analysis":

                    figures, analysis_texts, = self.analysis_handler.basic_analysis(self.request)

                case "comparison":
                    figures, analysis_texts = self.analysis_handler.comparison(self.request)

                case "predictions":
                    figures, analysis_texts = self.analysis_handler.predictions(self.request)

                case "significant_event_detection":
                    figures, analysis_texts = self.analysis_handler.significant_event_detection(self.request)

                case _:
                    analysis_texts = "Unexpected type of analysis provided! Received:" + analysis_type
                    logger.error(analysis_texts)
            
            with st.chat_message("assistant"):
                
                tab_names, analysis_header = self.create_tab_names(len(figures))
                st.header(analysis_header)
                # if len(figures)>1:
                    # Create tab names based on the number of figures
                
                tabs = st.tabs(tab_names)

                # Display each figure in its corresponding tab
                for tab, figure, analysis_text in zip(tabs, figures, analysis_texts):
                    with tab:
                        st.write(analysis_text)
                        if figure:
                            st.plotly_chart(figure)
                # else:    
                #     for analysis_text, figure in zip(analysis_texts, figures):
                    
                #         st.write(analysis_text)
                    
                #         if (figure):
                #             st.plotly_chart(figure)
                        
                st.session_state.messages.append({"role": "assistant", "analysis":{"analysis_header":analysis_header,"analysis_texts": analysis_texts, "plotly_charts": figures, 'tabs': tab_names}})



        else:
            logger.info("No analysis type was present.")
            
        if self.request.request_analysis[0] == 'predictions':
            pass
        else:
            with st.chat_message("assistant"):
                st.write("To view the animation, please use the optional generation button. Kindly be aware that loading may take some time. Also, if you search for new content while the animation is displayed, it will not be retained in your history due to the large loading process.")
                self.animation_header = f"Animation for locations: {', '.join(self.request.request_locations)}"
                if st.button("Generate Animation", on_click = self.output_animation):
                    st.write("your animation")
                
        
                    
                    
        
        # st.session_state.messages.append({"role": "assistant","animation_messages": { "animation" : animation, "button_state": button_clicked, "animation_header": animation_header}})


                
        
    def output_animation(self):
            st.session_state.click.append(True)
            st.session_state.messages.append({"role": "assistant","animation_messages": { "animation" : self.animation, "animation_header": self.animation_header}})
    
    def replace_last_entry(self):
        if st.session_state.past_request:
            st.session_state.past_request[-1] = self.request
    
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
                self.request.errors = []
                self.replace_last_entry()
                self.request.process_request()
            else:
                pass
        
    def check_climate_context(self):
        with st.chat_message("assistant"):
            non_climate_data = "Thanks for your request. However there is no climate context. Please provide more accurate information."
            st.write(non_climate_data)
            st.session_state.messages.append({"role": "assistant", "request_info": non_climate_data})
            st.stop()     
            
    def search_and_check_all_loc(self, locations, user_prompt):
        threshold = 70  # Define your threshold for fuzzy matching

        while locations and locations[0] not in ["None", None]:
            # Convert found locations to lowercase for case-insensitive comparison
            # Convert found locations to lowercase for case-insensitive comparison
            found_locations_lower = [loc.lower() for loc in locations]

            # Split the user prompt into words and convert to lowercase
            words_in_prompt = [word.lower() for word in user_prompt.split()]

            # Keep track of matches to clean from the user prompt
            matches_to_remove = []

            # Use fuzzy matching to find the best match for the found locations
            for loc in found_locations_lower:
                match, score, _ = process.extractOne(loc, words_in_prompt, scorer=fuzz.token_sort_ratio)
                if score >= threshold:
                    matches_to_remove.append(loc)  # Store the location, not the word from prompt, for case consistency
                    print(f'Match: {loc} with score: {score}')

            # Clean the user prompt based on found matches
            cleaned_prompt = user_prompt
            for match in matches_to_remove:
                # Remove matched terms from the cleaned_prompt, using case-insensitive matching
                cleaned_prompt = re.sub(r'\b' + re.escape(match) + r'\b[,\s]*', '', cleaned_prompt, flags=re.IGNORECASE)

            # Remove "and" if it's left with dangling commas or spaces
            cleaned_prompt = re.sub(r'\band\b[,\s]*', '', cleaned_prompt, flags=re.IGNORECASE)

            # Handle leftover commas, spaces, or "and" 
            cleaned_prompt = re.sub(r'\s*,\s*', ', ', cleaned_prompt)  # Ensure single comma with a space after it
            cleaned_prompt = re.sub(r',\s*$', '', cleaned_prompt)  # Remove trailing commas
            cleaned_prompt = re.sub(r'\s+', ' ', cleaned_prompt)  # Remove extra spaces
            cleaned_prompt = cleaned_prompt.strip()  # Remove leading/trailing spaces

            print("Cleaned Prompt:", cleaned_prompt)
                        
            # Retrieve new locations from the cleaned prompt
            found_location = self.prompt_manager.retrieve_information("location_agent", cleaned_prompt)
            is_location = self.prompt_manager.retrieve_information("binary_location_detection", found_location[0])

            if is_location[0] == 'False':
                return locations
            else:
                # Check if the new found location is not already in the existing found locations
                if found_location[0].lower() not in found_locations_lower:
                    locations.append(found_location[0])

        return locations  # Return locations when loop is complete
    
    def analysis_compatability(self):
        now = datetime.now()
        date_str = now.strftime('%Y')
        if self.request.request_timeframes[0] != "None":
            for timeframe in self.request.request_timeframes:
                if self.request.request_analysis[0] == 'basic_analysis' or self.request.request_analysis[0] == 'comparison':
                    if timeframe.startdate.year >= now.year or timeframe.enddate.year >= now.year:
                        with st.chat_message("assistant"):
                            analysis_incompatability = f"The {self.request.request_analysis[0]} cannot be shown for the current year: {date_str} and the following years. Please try another time frame"
                            st.write(analysis_incompatability)
                            st.session_state.messages.append({"role": "assistant", "request_info": analysis_incompatability})
                            st.stop()
                elif self.request.request_analysis[0] == 'predictions':
                    if timeframe.prediction_startdate.year < now.year or timeframe.prediction_enddate.year < now.year:
                        with st.chat_message("assistant"):
                            analysis_incompatability = f"The {self.request.request_analysis[0]} cannot be shown for the previous years before {date_str}. Please try a timeframe towards the future!"
                            st.write(analysis_incompatability)
                            st.session_state.messages.append({"role": "assistant", "request_info": analysis_incompatability})
                            st.stop()
                            
    def create_tab_names(self, len_figures):
        if self.request.request_analysis[0] == 'basic_analysis':
            tab_names = []
            for sub_request in self.request.collected_sub_requests:
                if sub_request.timeframe_object.startdate.year != sub_request.timeframe_object.enddate.year:
                    tab_name = f"{sub_request.location} {sub_request.timeframe_object.startdate.year}-{sub_request.timeframe_object.enddate.year}" 
                    
                else:
                    tab_name = f"{sub_request.location} {sub_request.timeframe_object.startdate.year}" 
                
                tab_names.append(tab_name)
            analysis_header = 'Basic Analysis'
            return tab_names, analysis_header
        
        elif self.request.request_analysis[0] == 'predictions':
            tab_names = [f"{self.request.collected_sub_requests[i].location} {self.request.collected_sub_requests[i].timeframe_object.prediction_startdate.year}-{self.request.collected_sub_requests[i].timeframe_object.prediction_enddate.year}" for i in range(len_figures)]
            analysis_header = 'Prediction'
            return tab_names, analysis_header
        
        elif self.request.request_analysis[0] == 'comparison' and self.request.multi_loc_request:
            # Concatenate location names and date ranges into a single tab
            locations = ' vs. '.join([sub_request.location for sub_request in self.request.collected_sub_requests])
            if self.request.collected_sub_requests[0].timeframe_object.startdate.year != self.request.collected_sub_requests[0].timeframe_object.enddate.year:
                date_ranges = f"{self.request.collected_sub_requests[0].timeframe_object.startdate.year}-{self.request.collected_sub_requests[0].timeframe_object.enddate.year}"
            else:
                date_ranges = f"{self.request.collected_sub_requests[0].timeframe_object.startdate.year}"
            tab_names = [f"{locations} in {date_ranges}"]
            analysis_header = 'Comparison over Location'
            return tab_names, analysis_header
        elif self.request.request_analysis[0] == 'comparison' and self.request.multi_time_request:
            # Concatenate timeframes into a single tab (assuming the same location for multiple timeframes)
            location = self.request.collected_sub_requests[0].location
            date_ranges = []  # To accumulate the formatted date ranges

            for sub_request in self.request.collected_sub_requests:
                if sub_request.timeframe_object.startdate.year != sub_request.timeframe_object.enddate.year:
                    date_range = f"{sub_request.timeframe_object.startdate.year}-{sub_request.timeframe_object.enddate.year}"
                else:
                    date_range = f"{sub_request.timeframe_object.startdate.year}"
                    
                date_ranges.append(date_range)  # Add the formatted range to the list
        
            # Concatenate the date ranges with ' vs. ' to show comparison
            concatenated_date_ranges = ' vs. '.join(date_ranges)
            tab_names = [f"{location} {concatenated_date_ranges}"]
            analysis_header = 'Comparison over Time'
            return tab_names, analysis_header
from cda_classes.chatbot import Chatbot
import streamlit as st
import jsonpickle
import os
from streamlit_extras.bottom_container import bottom
from datetime import datetime, timedelta

# @st.cache_resource    
# def load_chatbot():
#     chatbot = Chatbot()
#     return chatbot

class EOChatBot():
    def __init__(self):
        # Init stuff
        self.chatbot = Chatbot()

    def run(self):

        # streamlit chatbot interface with chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if 'past_request' not in st.session_state:
            st.session_state.past_request = []
        if "click" not in st.session_state:
            st.session_state.click = []

        while len(st.session_state.click) < len(st.session_state.messages):
            st.session_state.click.insert(0, False)
        
        for idx, message in enumerate(st.session_state.messages):

            with st.chat_message(message["role"]):
                if message.get("prompt"):
                    st.markdown(message["prompt"], unsafe_allow_html=True)
                    
                elif message.get("request_info"):
                    st.write(message["request_info"])   
                                 
                elif message.get("analysis"):
                    analysis = message["analysis"]
                    st.header(analysis["analysis_header"])
                    st.write(analysis["analysis_message"])
                    st.plotly_chart(analysis["plotly_chart"])
                    
                elif st.session_state.click[idx] == True:

                # elif message.get("animation_messages"):
                    animation_messages = message["animation_messages"]
                    
                #     st.write("To view the animation, please use the optional generation button. Kindly be aware that loading may take some time. Also, if you search for new content while the animation is displayed, it will not be retained in your history due to the large loading process.")
                #     button_state = animation_messages["button_state"]
                #     if button_state:
                    st.header(animation_messages["animation_header"])
                    st.plotly_chart(animation_messages["animation"])
                    st.session_state.click[idx] = False
                    del st.session_state.messages[idx]["animation_messages"]
                    del st.session_state.messages[idx]
                
        if not st.session_state.messages:        
            with st.chat_message('assistant'):
                st.write("Please look up first the documentation of the Climate Data Agent to asure the correct usecase!")
                    


        st.markdown("""
            <style>
            /* Target the sidebar's collapsed button */
            [data-testid="collapsedControl"] .st-emotion-cache-yfhhig.ef3psqc5 {
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: #800020; /* Burgundy red background */
                color: white; /* White text */
                padding: 10px;
                border-radius: 5px; /* Rounded corners */
                cursor: pointer; /* Pointer/hand icon */
                width: auto; /* Auto width to fit text */
            }

            /* Hide the default SVG icon inside the collapsed button */
            [data-testid="collapsedControl"] .st-emotion-cache-yfhhig.ef3psqc5 svg {
                display: none;
            }

            /* Add custom text to the collapsed button */
            [data-testid="collapsedControl"] .st-emotion-cache-yfhhig.ef3psqc5::before {
                content: 'Documentation';
                font-size: 16px;
                color: white;
            }

            /* Change background on hover for the collapsed button */
            [data-testid="collapsedControl"] .st-emotion-cache-yfhhig.ef3psqc5:hover {
                background-color: #660018; /* Darker burgundy red on hover */
            }
            </style>
            """, unsafe_allow_html=True)
        
        
        variable_list = ["2m Temperature", "Skin Temperature", "Total Precipitation", "10m Wind Speed", "Snow Depth", "Evapuration"]
        variable_explanations = {
            "2m Temperature": "Temperature of air at 2m above the surface of land, sea or in-land waters. 2m temperature is calculated by interpolating between the lowest model level and the Earth's surface, taking account of the atmospheric conditions. ",
            "Skin Temperature": "Temperature of the surface of the Earth. The skin temperature is the theoretical temperature that is required to satisfy the surface energy balance. It represents the temperature of the uppermost surface layer, which has no heat capacity and so can respond instantaneously to changes in surface fluxes. Skin temperature is calculated differently over land and sea.",
            "Total Precipitation": "Accumulated liquid and frozen water, including rain and snow, that falls to the Earth's surface. It is the sum of large-scale precipitation (that precipitation which is generated by large-scale weather patterns, such as troughs and cold fronts) and convective precipitation (generated by convection which occurs when air at lower levels in the atmosphere is warmer and less dense than the air above, so it rises). Precipitation variables do not include fog, dew or the precipitation that evaporates in the atmosphere before it lands at the surface of the Earth.",  
            "10m Wind Speed": "This parameter is the horizontal speed of the wind, or movement of air, at a height of ten metres above the surface of the Earth.",
            "Snow Depth": "Instantaneous grib-box average of the snow thickness on the ground (excluding snow on canopy).",
            "Evapuration": "Accumulated amount of water that has evaporated from the Earth's surface, including a simplified representation of transpiration (from vegetation), into vapour in the air above."  
        }
        # Get today's date
        today = datetime.now()

        # Calculate the date 7 days ago
        seven_days_ago = today - timedelta(days=7)
        
        time_period_list = ["From", "01-01-1950", "To", seven_days_ago.strftime('%d-%m-%Y')]

        st.sidebar.title('Documentation')

        # Variables section
        with st.sidebar:
            st.subheader("Available Variables - ERA-5-Land")
            
            row1 = st.columns(3)
            row2 = st.columns(3)
            for idx, col in enumerate(row1 + row2):
                if idx < len(variable_list):
                    variable = variable_list[idx]
                    with col:
                        with st.popover(variable, use_container_width=30):
                            st.write(variable_explanations.get(variable, "No explanation available."))

            st.write(" ")
            st.subheader("Available Locations")
            with st.container(border = True):
                st.write("Every Location is possible! Please try to use the correct name.")

            st.subheader("Available Time")
            
            row3 = st.columns(4)
            for idx, col in enumerate(row3):
                if idx < len(time_period_list):
                    with col:
                        tile = col.container(height=50)
                        tile.write(time_period_list[idx])
            
            analysis_type_list = ["Basic Analysis", "Comparison", "Prediction"]
            analysis_type_explanations = {
                "Basic Analysis": (
                    "Basic Analysis provides fundamental statistical insights into the dataset and is the default mode when no Analysis Type was selected. "
                    "It includes the calculation of the minimum and maximum values, as well as the standard deviation. "
                    "This analysis is useful for understanding the overall range and variability of the data."
                ),
                "Comparison": (
                    "Comparison analysis allows for the evaluation of differences between multiple data points. "
                    "It can compare data across different locations or between different time periods. "
                    "For multi-location comparisons, it visualizes data from multiple locations side-by-side. "
                    "For multi-time comparisons, it contrasts data from two distinct time ranges to identify temporal changes."
                ),
                "Prediction": (
                    "Prediction analysis uses historical data to forecast future trends. "
                    "By applying predictive modeling techniques, such as time series forecasting with Prophet, "
                    "this analysis generates predictions for a specified future period. "
                    "The output includes forecasted data points along with a confidence interval for each prediction."
                ),
            }
            
            st.subheader("Available Analysis Types")
            row4 = st.columns(3)
            for idx, col in enumerate(row4):
                if idx < len(analysis_type_list):
                    with col:
                        analysis_type = analysis_type_list[idx]
                        with st.popover(analysis_type, use_container_width=30):
                            st.write(analysis_type_explanations.get(analysis_type, "No explanation available."))
                            
                            
                            
            container1 = st.container(border=True)
            container2 = st.container(border=True)
            container3 = st.container(border=True)
                            
            st.header("Examples")
            container_data = [
                "Show me the Temperature of Rome between 2015 and 2020",
                "Compare the Precipitation of Rome and London between 2015 and 2020",
                "Show me a Prediction of the Temperature of London between 2020 to 2023"
            ]
            for idx, prompt in enumerate(container_data):
                container = st.container(border=True)
                with st.popover(f"{prompt}", use_container_width=100):
                    st.write(f"{prompt}")
                
        request_complete = False        
        

        
        
        with bottom():
            chat_col, button_col = st.columns([4, 1])
            

            # Get User Input
            with chat_col:
                if (user_message := st.chat_input('user')):
                    st.session_state.messages.append({"role": "user", "prompt": user_message})
                
                    
            with button_col:
                if st.button("Clear Chat"):
                    st.session_state.messages = []    
                    st.session_state.click = []
                    st.rerun()                

        if user_message:            
            with st.chat_message("user"):
                st.markdown(user_message)
                        
            self.chatbot.process_request(user_message)
            
   
            # request_complete = True

        if (request_complete):
            self.chatbot.execute_request()
            self.chatbot.output_results()
            request_complete = False
            st.stop()



if __name__ == "__main__":
    eo_chatbot = EOChatBot()
    eo_chatbot.run()
    

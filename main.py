from cda_classes.chatbot import Chatbot
import streamlit as st
import jsonpickle
import os
from streamlit_extras.bottom_container import bottom
from datetime import datetime, timedelta
from streamlit_app.sidebar import sidebar
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
            with st.container(border=True):      
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
        



        st.sidebar.title('Documentation')

        # Variables section
        with st.sidebar:
            sidebar()

                
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
    

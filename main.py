from cda_classes.chatbot import Chatbot
import streamlit as st
import jsonpickle
import os
from streamlit_extras.bottom_container import bottom

# @st.cache_resource    
# def load_chatbot():
#     chatbot = Chatbot()
#     return chatbot

class EOChatBot():
    def __init__(self):
        # Init stuff
        self.i = 0
        self.chatbot = Chatbot()

    def run(self):

        # streamlit chatbot interface with chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if 'past_request' not in st.session_state:
            st.session_state.past_request = []
            
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message.get("content"):
                    st.markdown(message["content"], unsafe_allow_html=True)
                if message.get("video"):
                    st.video(message["video"])


                    
        request_complete = False


        with bottom():
            chat_col, button_col = st.columns([4, 1])
            

            # Get User Input
            with chat_col:
                if (user_message := st.chat_input('user')):
                    st.session_state.messages.append({"role": "user", "content": user_message})
                    
            with button_col:
                if st.button("Clear Chat"):
                    st.session_state.messages = []    
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
    

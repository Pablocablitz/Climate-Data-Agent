from cda_classes.chatbot import Chatbot
import streamlit as st
import json
import jsonpickle

class EOChatBot():
    def __init__(self):
        # Init stuff

        self.chatbot = Chatbot()

    def run(self):
        request_complete = False

        # Get User Input
        if (user_message := st.chat_input('user')):
            self.chatbot.process_request(user_message)
            st.write(jsonpickle.encode(self.chatbot.request))
            user_message = None

            # request_complete = True
        # Process user Input
        # Output user input

        if (request_complete):
            self.chatbot.execute_request()
            self.chatbot.output_results()
            request_complete = False
            st.stop()



if __name__ == "__main__":
    eo_chatbot = EOChatBot()
    eo_chatbot.run()
    

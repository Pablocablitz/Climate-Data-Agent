from chatbot import Chatbot
import streamlit as st


class EOChatBot():
    def __init__(self):
        # Init stuff

        self.chatbot = Chatbot()

    def run(self):

        while True:
            # Get User Input
            if (user_message := st.chat_input()):
                self.chatbot.process_request(user_message)
                user_message = None

                request_complete = True
            # Process user Input
            # Output user input

            if (request_complete):
                self.chatbot.execute_request()
                self.chatbot.output_results()
                request_complete = False



if __name__ == "__main__":
    eo_chatbot = EOChatBot()
    eo_chatbot.run()
    

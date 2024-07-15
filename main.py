
from llm_processor import LargeLanguageModelProcessor
from llm_agent import LargeLanguageModelAgent
from chatbot import Chatbot
from data_handler import DataHandler
import streamlit as st


class EOChatBot():
    def __init__():
        # Init stuff
        llama3 = LargeLanguageModelProcessor()
        chatbot = chatbot()

    def run():

        while True:
            # Get User Input
            if (user_message := st.chat_input()):
                chatbot.process_request(user_message)
                user_message = None
            # Process user Input
            # Output user input

            if (request_complete):
                process_request() # data download, data processing, analysis...
                output_results()



if __name__ == "__main__":
    eo_chatbot = EOChatBot()
    eo_chatbot.run()
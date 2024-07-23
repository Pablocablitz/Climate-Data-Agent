from cda_classes.chatbot import Chatbot
import streamlit as st
import jsonpickle

class EOChatBot():
    def __init__(self):
        # Init stuff
        self.i = 0
        self.chatbot = Chatbot()

    def run(self):
        self.i = self.i +1
        print(self.i)
        # streamlit chatbot interface with chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "request" not in st.session_state:
            st.session_state.past_request = []
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message.get("content"):
                    st.markdown(message["content"], unsafe_allow_html=True)
                if message.get("video"):
                    st.video(message["video"])

                    
        request_complete = False

        # Get User Input
        if (user_message := st.chat_input('user')):
            st.session_state.messages.append({"role": "user", "content": user_message})
            with st.chat_message("user"):
                st.markdown(user_message)
                
            self.chatbot.process_request(user_message)
            
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
    

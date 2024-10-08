import streamlit as st

from streamlit_extras.bottom_container import bottom
from streamlit_app.sidebar import sidebar
from cda_classes.chatbot import Chatbot

class EOChatBot:
    def __init__(self):
        # Initialize Chatbot instance
        self.chatbot = Chatbot()

    def run(self):
        # Initialize chat-related session states
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "past_request" not in st.session_state:
            st.session_state.past_request = []
        if "click" not in st.session_state:
            st.session_state.click = []

        while len(st.session_state.click) < len(st.session_state.messages):
            st.session_state.click.insert(0, False)

        # Display chat history
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                if message.get("prompt"):
                    st.markdown(message["prompt"], unsafe_allow_html=True)
                elif message.get("request_info"):
                    st.markdown(
                        message["request_info"], unsafe_allow_html=True
                    )
                elif message.get("analysis"):
                    analysis = message["analysis"]
                    tab_names = analysis["tabs"]
                    st.header(analysis["analysis_header"])
                    tabs = st.tabs(tab_names)
                    for tab, figure, analysis_text in zip(
                        tabs, analysis["plotly_charts"], analysis["analysis_texts"]
                    ):
                        with tab:
                            st.write(analysis_text)
                            if figure:
                                st.plotly_chart(figure)
                elif st.session_state.click[idx] is True:
                    animation_messages = message["animation_messages"]
                    st.header(animation_messages["animation_header"])
                    st.plotly_chart(animation_messages["animation"])
                    st.session_state.click[idx] = False
                    del st.session_state.messages[idx]["animation_messages"]
                    del st.session_state.messages[idx]

        if not st.session_state.messages:
            with st.container(border=True):
                with st.chat_message("assistant"):
                    st.write(
                        "Please refer to the Climate Data Agent documentation to "
                        "ensure correct usage. Thank you!"
                    )

        # Customized Sidebar button styles
        st.markdown(
            """
            <style>
            /* Target the sidebar's collapsed button */
            [data-testid="collapsedControl"] .st-emotion-cache-yfhhig.ef3psqc5 {
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: #800020;
                color: white;
                padding: 10px;
                border-radius: 5px;
                cursor: pointer;
                width: auto;
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
                background-color: #660018;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # Sidebar content
        with st.sidebar:
            sidebar()

        # Bottom container for user input
        with bottom():
            chat_col, button_col = st.columns([4, 1])

            # Get User Input
            with chat_col:
                user_message = st.chat_input("user")
                if user_message:
                    st.session_state.messages.append(
                        {"role": "user", "prompt": user_message}
                    )

            # Button to clear chat
            with button_col:
                if st.button("Clear Chat"):
                    st.session_state.messages = []
                    st.session_state.past_request = []
                    st.session_state.click = []
                    st.rerun()

        # Process user input message
        if user_message:
            with st.chat_message("user"):
                st.markdown(user_message)
            self.chatbot.process_request(user_message)


if __name__ == "__main__":
    eo_chatbot = EOChatBot()
    eo_chatbot.run()

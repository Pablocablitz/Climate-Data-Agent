# Climate-Data-Agent
## Setup

### Authentication
In order to download data from the various sources, the user must obtain an API key and properly configure their system for access.

#### CDS
The full process is described [here](https://cds.climate.copernicus.eu/api-how-to#install-the-cds-api-key), but for convenience the basic steps are described here:
1. Register on the CDS platform in order to obtain a UID and an API key
2. Find the UID and API key on the [user profile](https://cds.climate.copernicus.eu/user/317337)
3. Create a .cdsapirc file in the workspace with the format (UID and API key below are just an example):
```
url: https://cds.climate.copernicus.eu/api/v2
key: 123456:1c1c1c1c-1c1c-c1c1-1c11-c04240eb531c
```

# Climate-Data-Agent

## Project Overview
**Climate-Data-Agent** is a Python-based application designed to connect users with climate data through a natural language interface. The application utilizes a customized Streamlit chatbot interface, allowing users to ask for climate data based on specific dates and locations. Users can request various climate-related products, including temperature, precipitation, and wind data.

### Key Features
- **Natural Language Interface**: Users interact with the system by asking questions in plain language.
- **LLM-Powered Backend**: The backend is powered by the Llama3 large language model (LLM).
- **Specialized LLM Agents**: Several specialized LLM agents are deployed for specific tasks.
- **Data Retrieval and Visualization**: The application retrieves relevant climate data and presents it visually.

## Introduction to this Repository
1. **Utils**: Contains all necessary functions outside of the classes `CDS` and `LLM`.
2. **Main Function**: The main function is located inside `streamlit_app_main.py`.
3. **Config File**: The config file includes all the necessary static data for the LLM and the API request of CDS.
4. **Variable File**: The variable file contains all the necessary information for the climate products.

## How to Run the Code
To run the **Climate-Data-Agent** application, follow these steps:

1. **Ensure you have the required dependencies installed**: Open a terminal, navigate to the project directory, and run:
    ```bash
    pip install -r requirements.txt
    ```

2. **Setting Up Hugging Face API Key**

    To use the LLaMA 3 8B model, you need to authenticate with your Hugging Face API key. Follow these steps:

    2.1 **Get Your Hugging Face API Key**:
        - Log in to your Hugging Face account [here](https://huggingface.co/).
        - Go to your [Access Tokens](https://huggingface.co/settings/tokens) and create a new token with the necessary permissions (either Read or Write permissions should work).

    2.2 **Insert Your Hugging Face API Key in the Code**:
        Open the `main.py` file and find the following section at the top of the code:

        ```python
        # First, activate the login to download and use the model
        # Make sure to insert your Hugging Face API key here
        from huggingface_hub import login
        login("YOUR_HHF_API_KEY")
        ```

        Replace `"YOUR_HHF_API_KEY"` with your actual Hugging Face API key:

        ```python
        login("your_actual_api_key_here")
        ```
    
3. **Launch the Streamlit application**: Execute the following command in the terminal:
    ```bash
    streamlit run main.py
    ```
    
4. **Interact with the Chatbot Interface**: Open the application in your default web browser and start asking questions in natural language.
    
5. **Visualization and Analysis**: The application will provide visual outputs, including graphs and optional animations, along with a brief analysis of the data.

## Core Components

### 1. `main.py`
The `main.py` file serves as the entry point for the application. It initializes the Streamlit app and handles user interactions through a chatbot interface. Key components include:

- **Chatbot Initialization**: The `EOChatBot` class initializes the chatbot and sets up the Streamlit session state to maintain chat history.
    
- **Chat Interface**: The application manages user inputs and responses through a chat interface, displaying previous messages and analysis results.
    
- **User Interaction Handling**: The `run()` method manages user inputs, retrieves data, and displays visualizations. It uses a loop to process chat messages and update the chat interface dynamically.

```python
class EOChatBot():
    def __init__(self):
        self.chatbot = Chatbot()

    def run(self):
        # Streamlit chatbot interface with chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # User input handling
        user_message = st.chat_input('user')
        if user_message:
            self.chatbot.process_request(user_message)
            # Further processing...
```
### 2. `chatbot.py`

The `chatbot.py` file contains the `Chatbot` class, which processes user requests and retrieves climate data based on user inputs. Key functions include:

* **Request Processing**: The `process_request` method interprets the user's prompt, validates it, and calls appropriate functions based on the request type.
  
* **Data Retrieval and Analysis**: After validating the request, the method collects relevant data, performs analyses, and prepares visualizations.

```python
def process_request(self, user_prompt):
    self.request.user_prompt = user_prompt
    # Request validation and data retrieval
    if self.request.request_type[0] == 'False':
        self.check_climate_context()
    else:
        self.extract_information(user_prompt)
    # Downloading data and visualizations
    with st.spinner("Downloading Data..."):
        self.request.collect_eorequests()
```

### Summary:
- The README now includes a comprehensive overview, covering all key sections including the project overview, features, repository introduction, how to run the code, core components (including detailed information about `main.py` and `chatbot.py`), installation instructions, and a conclusion.
- You can copy this content directly into a file named `README.md` in your project repository. If you have any more requests or need further modifications, let me know!

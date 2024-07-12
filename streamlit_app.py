# app.py


import streamlit as st
import os
from loguru import logger
from utils import load_config, convert_to_variable_names, generate_climate_animation, generate_descriptions, update_non_none_values
from llm_class import LLM 
from cds_class import CdsERA5
# Load configuration files



# Function to perform the initial review processing
def process_review():
    
    # Use detect_location_agent to get the location and time information
    geo_information = llm.get_geo_information()
    logger.info(f"Geo Information: {geo_information}")
    
    # Get product information    
    product_information = llm.get_product_information()
    logger.info(f"Product Information: {product_information}")
    # Dictionary to store specific product information
    results = {}

    # Loop through the product information and get the specific product information
    for key, value in product_information.items():
        if value and value.lower() != "None":
            category = value.capitalize()
            product_list = [product['name'] for product in variables_config.get(category, [])]

            # Get specific product information   
            specific_product_information = llm.get_specific_product_information(product_list, category)
            
            if specific_product_information and 'chosen_product' in specific_product_information:
                results[key] = specific_product_information['chosen_product']
            else:
                logger.warning(f"No specific product information found for category {category}")

    # Print results
    logger.info(f"Results: {results}")

    # Gather variables into a list
    variables = [value for value in results.values()]
    variable_names = convert_to_variable_names(variables, variables_config)
    logger.info(f"Variables: {variable_names}")

    return product_information, geo_information, variable_names

# Function to perform the data processing and visualization
def process_data(geo_information, variable_names):
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    # Initialize CdsERA5 and update request
    cds = CdsERA5(config)
    updated_query = cds.update_request(geo_information, variable_names) 

    # Download data from CDS
    try:
        cds.get_data(query=updated_query)
        cds.download(filename="ERA5")
    except Exception as e:
        return f"Issue in the data access or download: {e}", None

    # Process the data
    ds, variable_names = cds.process()

    # Display animation for selected variable
    
    for variable_name in variable_names:
        ds, category, units, name = llm.data_processing(ds, variables_config, variable_name)
        month, monthly_means = cds.calculate_monthly_means(ds, variable_name, category)
        logger.info("successfully calculate monthly means.")
        animation = generate_climate_animation(ds[variable_name], category, units, updated_query, name, variables_config)
        logger.info("successfully generate climate animation.")
        video_path = animation  # Update with correct path to your animation file

        # Display descriptions
        descriptions = generate_descriptions(month, monthly_means, units, category)
        
        descriptions_text = "\n".join([f"Year {year}: {temp} " for year, temp in descriptions.items()])
        print(descriptions_text)
        # set your agent 
        agent_analysis = f'{category}_analysis'
        
        analysis = llm.set_agent(agent_analysis, descriptions_text)
        return analysis, video_path

# Cache the LLM model
@st.cache_resource    
def load_llm(config):
    llm = LLM(config)
    return llm

# MAIN
dir_path = os.path.dirname(os.path.realpath(__file__))
config = load_config(file_path=os.path.join(dir_path, "config.yaml"))   
variables_config = load_config(file_path=os.path.join(dir_path, "variables.yaml"))
llm_config = config["llm_info"]

# Initialize Streamlit app
st.title('Climate Data Analysis Application')
os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
llm = load_llm(llm_config)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)
        if message.get("video"):
            st.video(message["video"])
        if message.get("label"):
            st.download_button(
                message["label"],
                message["data"],
                message["file_name"])
            
# Initialize session state variables
if "variables" not in st.session_state:
    st.session_state.variables = []
    
if "geo_information" not in st.session_state:
    st.session_state.geo_information = {}
    
if "product_information" not in st.session_state:
    st.session_state.product_information = {}

if 'context_flag' not in st.session_state:
    st.session_state.context_flag = False
    
if user_message := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_message})
    
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(user_message)
    
    # pass the user messsage to the model class
    llm.get_user_message(user_message)
    
    # check if user searches for climate data
    context_agent = "detect_if_climate_data"
    user_interest = llm.climate_data_context(context_agent)
    decision = user_interest["climate_data"]
    
    if decision == "True":
        
        # Process user message to get the review information
        product_information, geo_information, variable_names = process_review()    
        print(variable_names)

        # Update session state with the new information
        st.session_state.geo_information = update_non_none_values(geo_information, st.session_state.geo_information)
        st.session_state.product_information = update_non_none_values(product_information, st.session_state.product_information)
        
        # Filter out "None" values
        st.session_state.variables = [var for var in st.session_state.variables if var != "None"]

        # If variables list is empty or contains only "None", extend it with new variables
        if not st.session_state.variables:
            st.session_state.variables.extend(variable_names)
        
        # Checks if user data is complete if not stops execution and jump back to the user with notification about the missing info
        review = llm.get_review_request(st.session_state.variables, st.session_state.geo_information, st.session_state.product_information)     
        data_review = review.get("data")
        status_review = review.get("status")
        
        # Display review information
        with st.chat_message("assistant"):
            st.write(data_review)
        # Add review information to chat history
        st.session_state.messages.append({"role": "assistant", "content": data_review})
        if status_review == "information_notification":
            
            st.stop()  # Stop execution here and wait for the next user input

        # Process data and get the response and video path
        with st.spinner("Downloading Data..."):
            response, video_path = process_data(st.session_state.geo_information, st.session_state.variables)
        
        location = st.session_state.geo_information["location"]
        variables = st.session_state.variables[0]
        start_year = st.session_state.geo_information["start_year"]
        end_year = st.session_state.geo_information["end_year"]
        
        # reset states
        st.session_state.geo_information = {}
        st.session_state.product_information = {}
        st.session_state.variables = []
        
        # Display assistant response and video in chat message container
        with st.chat_message("assistant"):
            st.write(response)
            if video_path:
                st.video(video_path)
            st.download_button(
                label="Download Animation",
                data=video_path,
                file_name=f"Animation_{variables}_{location}_{start_year}_{end_year}.mp4",    
            )
                
        # Add assistant response and video to chat history
        st.session_state.messages.append({"role": "assistant", "content": response, "video": video_path, "label": "Download Animation", "data": video_path,"file_name": f"Animation_{variables}_{location}_{start_year}_{end_year}.mp4"})
    else:
        # Answer the Question with General Knowledge of LLama3
        q_a_agent = "QandA_general"
        q_a_response = llm.general_response(q_a_agent)
        with st.chat_message("assistant"):
            st.write(q_a_response)
        
        st.session_state.messages.append({"role": "assistant", "content": q_a_response})



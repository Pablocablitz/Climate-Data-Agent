# app.py

import streamlit as st
import os
from loguru import logger
import xarray as xr
import json
import yaml

from utils import load_config, CdsERA5, LLM, clean_json_response, plot_means, calculate_annual_means, generate_descriptions, calculate_monthly_means, generate_climate_animation, separate_components, convert_to_variable_names

# Load configuration files
dir_path = os.path.dirname(os.path.realpath(__file__))
config = load_config(file_path=os.path.join(dir_path, "config.yaml"))   
variables_config = load_config(file_path=os.path.join(dir_path, "variables.yaml"))
llm_config = config["llm_info"]

# Initialize Streamlit app
st.title('Climate Data Analysis Application')

# Function to perform data processing and visualization
def process_data(user_message):
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    # Initialize LLM
    llm = LLM(llm_config, user_message)
    
    # Use detect_location_agent to get the location and time information
    agent_loc_ys = "detect_location_years"
    geo_information = llm.get_geo_information(agent_loc_ys)
    logger.info(f"Geo Information: {geo_information}")
    
    # Get product information    
    detect_product_agent = "Detect_product_type"
    product_information = llm.get_product_information(detect_product_agent)
    
    # Dictionary to store specific product information
    results = {}

    # Loop through the product information and get the specific product information
    for key, value in product_information.items():
        if value and value != "None":
            category = value.capitalize()
            product_list = [product['name'] for product in variables_config.get(category, [])]

            # Get specific product information   
            determine_specific_product_agent = "Determine_specific_product"
            specific_product_information = llm.get_specific_product_information(determine_specific_product_agent, product_list, category)
            
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

    # Initialize CdsERA5 and update request
    cds = CdsERA5(config)
    updated_query = cds.update_request(geo_information, variable_names) 
    output_folder = config["output_folder"]

    # Download data from CDS
    try:
        cds.get_data(query=updated_query)
        cds.download(filename="ERA5")
    except Exception as e:
        return f"Issue in the data access or download: {e}", None

    # Process the data
    ds, variable_names = cds.process()

    # Display animation for selected variable
    variable_name = st.selectbox("Select a variable to display animation:", variable_names)
    
    if variable_name:
        try:
            ds, category, units, name = llm.data_processing(ds, variables_config, variable_name)
            years, annual_means = calculate_monthly_means(ds, variable_name, category)
            animation = generate_climate_animation(ds[variable_name], category, units, updated_query, name, variables_config)
            video_path = "ERA_DATA/results/animation.mp4"  # Update with correct path to your animation file

            # Display descriptions
            descriptions = generate_descriptions(years, annual_means, units, category)
            
            descriptions_text = "\n".join([f"Year {year}: {temp} " for year, temp in descriptions.items()])
                
            # set your agent 
            agent_analysis = f'{category}_analysis'
            
            analysis = llm.set_agent(agent_analysis,  descriptions_text)
            return analysis, video_path

        except Exception as e:
            return f"Error processing variable '{variable_name}': {e}", None
    
    return "No variable selected.", None


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("video"):
            st.video(message["video"])

# Accept user input
if user_message := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_message})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(user_message)

    # Process user message and get the response
    response, video_path = process_data(user_message)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(response)
        if video_path:
            st.video(video_path)
        
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response, "video": video_path})

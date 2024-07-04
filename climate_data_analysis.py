from utils import load_config, CdsERA5, LLM, clean_json_response, plot_means, calculate_annual_means, generate_descriptions, calculate_monthly_means, generate_climate_animation, separate_components, convert_to_variable_names
import os 
from loguru import logger 
import xarray as xr
import json
import yaml


if __name__ == "__main__":
    
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    # Load configuration file
    config = load_config(file_path=os.path.join(dir_path,"config.yaml"))   
    variables_config = load_config(file_path=os.path.join(dir_path,"variables.yaml"))
    llm_config = config["llm_info"]
    
    user_message = input("Please enter your query:")
    
    # initialize the LLM
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
    
    
    cds = CdsERA5(config)
    updated_query = cds.update_request(geo_information, variable_names) 
    
    output_folder = config["output_folder"]
    out_dir = os.path.join(dir_path, output_folder, "cds")
    
    # setting apikey for coords
    
    out_dir = os.path.join(dir_path, output_folder,"cds")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    logger.info("start downloading data from CDS")
    
    # Get data
    try:
        cds.get_data(query = updated_query)
        cds.download(filename="ERA5")
    except Exception as e:
            logger.error(f"Issue in the data access or download: {e}")
    
    # Process the data
    ds, variable_names = cds.process()
    print(variable_names)
    
     
    out_dir2 = os.path.join(dir_path, output_folder,"animation.mp4")
    for variable_name in variable_names:
        # try:
        
        # Calculate annual means
        ds, category, units, name = llm.data_processing(ds, variables_config, variable_name)   
        # name, units, category = llm.get_details_from_short_name( variables_config, variable_name)
        years, annual_means = calculate_monthly_means(ds, variable_name, category)
        # Plot and save the results
        # plot_means(years, annual_means, variable_name, name, units, out_dir)
        animation = generate_climate_animation(ds[variable_name], category, units, updated_query, name, variables_config)
            
        # except Exception as e:
        #     logger.error(f"Error processing variable '{variable_name}': {e}")
            
        descriptions = generate_descriptions(years, annual_means, units, category)
        
        descriptions_text = "\n".join([f"Year {year}: {temp} " for year, temp in descriptions.items()])
            

        # set your agent 
        agent_analysis = f'{category}_analysis'
        print(agent_analysis)
        
        analysis = llm.set_agent(agent_analysis,  descriptions_text)

        print(analysis)
    

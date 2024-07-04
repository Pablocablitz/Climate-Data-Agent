"""
This Python utils file contains functions for data loading, preprocessing,
visualization data from CDS.
"""
import os
import cdsapi
import json
import xarray as xr
import numpy as np
import yaml
import pandas as pd
from loguru import logger
from matplotlib import pyplot as plt
from geopy.geocoders import GoogleV3
import transformers
import torch
from transformers import pipeline
import re 
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.animation import FuncAnimation
import googlemaps
from typing import Dict, List, Any



def load_config(file_path: str) -> dict:
    """
    Load YAML file.

    Args:
        file_path (str): Path to the YAML file.

    Returns:
        dict: Dictionary containing configuration information.
    """
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

def get_coordinates(location: str,  api_key: str) -> dict:
    """Get a bounding box for a location using Google Maps Geocoding API"""
    gmaps = googlemaps.Client(key=api_key)
    
    # Get place details
    geocode_result = gmaps.geocode(location)
    
    if geocode_result:
        viewport = geocode_result[0]['geometry']['viewport']
        bounding_box = {
            "north": viewport['northeast']['lat'],
            "south": viewport['southwest']['lat'],
            "east": viewport['northeast']['lng'],
            "west": viewport['southwest']['lng']
        }
        

        # Create a small bounding box around the location
        north = bounding_box["north"]
        south = bounding_box["south"]   
        west = bounding_box["west"]
        east = bounding_box["east"]
    
        return {"north": north, "west": west, "south": south, "east": east}
    else:
        return None
    
class CdsERA5:

    def __init__(self, config):
        """
                Initialize the CdsERA5 class.

        Parameters:
            config_path (str): Path to the configuration file.
        """
        try:
            self.client = cdsapi.Client()
            self.config = config
            logger.info("Successfully log to Climate Data Store")
        except:
            logger.error("Could not log to Climate Data Store")
            
    def update_request(self, data, variables):
        """
        Update the request in the configuration file.
        """
        query = self.config["cds_request"]
        # variables_string = variables[0]
        # cleaned_list = [item.strip().strip("'") for item in variables_string.split(',')]
        # variables = cleaned_list
        query["request"]["location_name"] = data["location"]
        query["request"]["start_year"] = data["start_year"]
        query["request"]["end_year"] = data["end_year"]
        query["request"]["variable"] = variables
        return query
        

    def get_data(self, query):
        """
        Retrieve data based on the query in the configuration file.
        """
        key = self.config["GOOGLE_API_KEY"]
        name = self.config["cds_request"]["name"]
        # Generate the list of years
        self.start_year = int(query["request"]["start_year"])
        self.end_year = int(query["request"]["end_year"])
        years = [str(year) for year in range(self.start_year, self.end_year + 1 )]

        # Generate the list of months
        months = query["request"]["month"]

        # Generate the area coordinates
        area = get_coordinates(query["request"]["location_name"], key)
        area = [area["north"], area["west"], area["south"], area["east"]]

        request = {
            "variable": query["request"]["variable"],
            "product_type": query["request"]["product_type"],
            "year": years,
            "month": months,
            "time": query["request"]["time"],
            "area": area,
            "format": query["request"]["format"]
        }
        
        # request = process_request(request)
        print(request)
        logger.info("request is ready")
        self.format = query["request"]["format"]
    
        self.result = self.client.retrieve(name, request)
        return self.result


    def download(self, filename):
        """
        """
        self.filename = f"{filename}.{self.format}"
        self.result.download(self.filename)
        
    def process(self):
        """
        Process the downloaded data.
        
        Returns:
            ds (xarray.Dataset): The processed dataset.
        """
        
        if self.format == "netcdf":
            ds = xr.open_dataset(self.filename, engine='netcdf4')
        elif self.format == "grib":
            ds = xr.open_dataset(self.filename, engine="cfgrib")
        else:
            raise ValueError(f"Unsupported format: {self.format}")

        if 'v10' in ds and 'u10' in ds:
            # Compute 'w10' as the magnitude of (u10, v10)
            w10 = np.sqrt(ds['u10']**2 + ds['v10']**2)
            
            # Add 'w10' to the dataset
            ds['w10'] = w10
            
            # Remove 'v10' and 'u10' from the dataset
            ds = ds.drop_vars(['v10', 'u10'])
            # Update variable_names to include 'w10'
            variable_names = list(ds.data_vars)
        else:
            variable_names = list(ds.data_vars)

        return ds, variable_names
    
    
    

def save_results(data: dict, filename: str):
    """
    Save a dictionary to a JSON file.

    Parameters:
        data (dict): Dictionary to be saved.
        filename (str): Name of the JSON file to save.

    Returns:
        None
    """
    with open(filename, 'w') as json_file:
        json.dump(data, json_file)
        

    
class LLM:
    def __init__(self, llm_config: dict, user_message: str):
        """
        Initialize the LLM class.
        """
        self.llm = llm_config["model_name"]
        self.prompt = user_message
        self.system_prompts = llm_config["system_prompts"]
        self.pipeline = transformers.pipeline(
            "text-generation",
            model=self.llm,
            device=0 if torch.cuda.is_available() else -1,  # Use GPU if available
            model_kwargs={"torch_dtype": torch.float16 if torch.cuda.is_available() else torch.bfloat16},
        )
    def agent(self, ag, descriptions_text = None, category = None , product_list = None):
        """
        get Response on your input prompt and system prompt
        """
        system_prompt = ag.format(prompt = self.prompt, descriptions_text = descriptions_text,  category = category, product_list = product_list)
        # print(system_prompt)
        messages = [
            {"role": "system", "content": system_prompt},
        
        ]
        # Generate the response
        outputs = self.pipeline(
        messages,
        max_new_tokens = 4000,
        do_sample = True,
        temperature = 0.5,
        top_p=0.95,
        )

        # Extract the generated text
        response = outputs[0]["generated_text"][-1]

        return response
    
    def set_agent(self, system_prompt: str, descriptions_text = None, product_list = None, category = None):
        """
        Detect the location information using the LLM agent.
        
        Returns:
            dict: The response content from the LLM agent.
        """
        system_prompt = self.system_prompts[system_prompt]
        
        try:
            response = self.agent(system_prompt, descriptions_text = descriptions_text, category = category, product_list = product_list)
        except Exception as e:
            logger.error(f"Issue in the LLM location configuration: {e}")
            
        text_response = response['content']
                
        return text_response
    
    def check_for_None(self, data):
        for key, value in data.items():
            if value == "None":
                data[key] = input(f"Please enter {key}: ")
        return data
    
    def get_details_from_short_name(self, data, short_name):
        for category, items in data.items():
            for item in items:
                if item.get('short_name') == short_name:
                    self.product = item.get('name')
                    self.units = item.get('units')
                    self.category = category
                    return self.product, self.units, self.category
        return None, None, None
    
    def data_processing(self, data, variables_config, variable):
        """
        Process the data to remove any missing values and convert temperature to Celsius.
        
        Parameters:
            data (xarray.Dataset): The data to be processed.
            category (str): The category of the data ("Temperature", "Precipitation", "Wind").
            variable_names (list): List of variable names to be processed.
        
        Returns:
            xarray.Dataset: The processed data.
        """    
    
        name, units, category = self.get_details_from_short_name(variables_config, variable)
        print(name, units, category)
        if category == "Temperature":
                # Convert temperature from Kelvin to Celsius
                data[variable] = data[variable] - 273.15
        
        elif category == "Precipitation":
                # Convert precipitation from meters to millimeters
                data[variable] = data[variable] * 1000
        
        return data, category, units, name
    
    def get_product_information(self, agent_name: str) -> Dict[str, Any]:
        try:
            product_info = self.set_agent(agent_name)
            return clean_json_response(product_info)
        except Exception as e:
            logger.error(f"Error getting product information with agent {agent_name}: {e}")
            return {}
    
    def get_specific_product_information(self, agent_name: str, product_list: List[str], category: str) -> Dict[str, Any]:
        try:
            specific_product_info = self.set_agent(agent_name, product_list=product_list, category=category)
            return clean_json_response(specific_product_info)
        except Exception as e:
            logger.error(f"Error getting specific product information for category {category} with agent {agent_name}: {e}")
            return {}
    
    def get_geo_information(self, agent_name: str) -> Dict[str, Any]:
        try:
            geo_info = self.set_agent(agent_name)
            geo_info = clean_json_response(geo_info)
            return self.check_for_None(geo_info)
        except Exception as e:
            logger.error(f"Error getting geo information with agent {agent_name}: {e}")
            return {}


def clean_json_response(response):
    """
    Cleans a JSON string by removing any content before the first `{` and after the last `}`.

    Args:
    response (str): The raw JSON response string.

    Returns:
    dict: A dictionary parsed from the cleaned JSON string.
    """
    # Find the first '{' and last '}'
    start_idx = response.find('{')
    end_idx = response.rfind('}')
    
    if start_idx == -1 or end_idx == -1:
        print("No JSON object found in the response.")
        return None
    
    # Extract the JSON string
    json_str = response[start_idx:end_idx + 1]
    
    # Replace single quotes with double quotes for valid JSON
    json_str = json_str.replace("'", '"')
    
    # Optionally, print the intermediate JSON string for debugging
    # print(json_str)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    
# def products_to_json
def calculate_annual_means(ds, variable_name, query, category):
    """
    Calculate annual mean values for a specified variable from the processed dataset.
    
    Parameters:
        ds (xarray.Dataset): The processed dataset.
        variable_name (str): The name of the variable to calculate the mean for.
        query (dict): The query dictionary containing the start and end years.

    Returns:
        years (list): List of years.
        annual_means (list): List of annual mean values.
    """
    # Calculate annual means by taking the mean of each year's data
    annual_mean = ds[variable_name].groupby('time.year').mean(dim='time')

    start_year = int(query["request"]["start_year"])
    end_year = int(query["request"]["end_year"])
    years = range(start_year, end_year + 1)
    annual_means = [annual_mean.sel(year=year).mean(dim=['latitude', 'longitude']).item() for year in years]

    # Print the dimensions to verify
    print(f"Annual mean {variable_name} dimensions: {annual_mean.shape}")

    # Print the annual means
    for year, mean_value in zip(years, annual_means):
        print(f"Year {year}: {mean_value:.2f}")

    return years, annual_means

def calculate_monthly_means(ds, variable_name, category):
    """
    Calculate monthly mean values for a specified variable from the processed dataset.
    
    Parameters:
        ds (xarray.Dataset): The processed dataset.
        variable_name (str): The name of the variable to calculate the mean for.

    Returns:
        months (list): List of months (formatted as 'YYYY-MM').
        monthly_means (list): List of monthly mean values.
    """
    # Calculate monthly means by taking the mean of each month's data
    monthly_mean = ds[variable_name].groupby('time.month').mean(dim='time')

    # Extract year and month from time coordinates for labeling
    months = ds['time'].dt.strftime('%Y-%m').values
    monthly_means = ds[variable_name].groupby('time.month').mean(dim=['latitude', 'longitude']).values

    # Print the dimensions to verify
    print(f"Monthly mean {variable_name} dimensions: {monthly_mean.shape}")

    # Print the monthly means
    for month, mean_value in zip(months, monthly_means):
        print(f"Month {month}: {mean_value:.2f}")

    return months, monthly_means
    
def plot_means(times, means, variable_name, name, units, output_dir, mean_type='annual'):
    """
    Plot and save mean values for a specified variable.
    
    Parameters:
        times (list): List of time points (years or months).
        means (list): List of mean values.
        variable_name (str): The name of the variable to plot.
        name (str): The display name of the variable.
        units (str): The units of the variable.
        output_dir (str): The directory where the plot will be saved.
        mean_type (str): Type of mean values ('annual' or 'monthly').
    """
    plt.figure(figsize=(10, 6))
    plt.plot(times, means, marker='o', linestyle='-')
    
    if mean_type == 'annual':
        plt.title(f'Annual Mean: {name}')
        plt.xlabel('Year')
    elif mean_type == 'monthly':
        plt.title(f'Monthly Mean: {name}')
        plt.xlabel('Month')
    
    plt.ylabel(f'{variable_name} ({units})')
    plt.grid(True)

    # Save the plot to the specified directory
    output_filename = f'{variable_name}_{mean_type}_mean.png'
    output_path = os.path.join(output_dir, output_filename)
    plt.savefig(output_path)
    plt.close()




def generate_descriptions(years, annual_means, units, category):
    """
    Generate descriptions for annual mean values with their corresponding units.
    
    Parameters:
        years (list of int): List of years.
        annual_means (list of float): List of annual mean values corresponding to each year.
        units (str): The units of the annual mean values.
    
    Returns:
        dict: A dictionary with years as keys and descriptions as values.
    """
    descriptions = {}
    for year, mean in zip(years, annual_means):
        descriptions[year] = f"{mean:.2f} {units}"
    return descriptions

def find_coord_name(coord_names, pattern):
    """
    Function to find coordinate names using regex

    """
    for name in coord_names:
        if pattern.search(name):
            return name
    return None

def Kelvin_to_Celsius(data):
    """
    Convert temperature data from Kelvin to Celsius.
    """
    return data - 273.15
    
    
    

def generate_climate_animation(climate_data, category, units, updated_query, name, variables_config):
    """
    Generate an animation of temperature data.
    """
    
    lat_pattern = re.compile(r'lat(itude)?', re.IGNORECASE)
    lon_pattern = re.compile(r'lon(gitude)?', re.IGNORECASE)
    coord_names = climate_data.coords.keys()
    lat_name = find_coord_name(coord_names, lat_pattern)
    lon_name = find_coord_name(coord_names, lon_pattern)
    

    
    # Define the wider area bounds (adjust these as needed)
    lon_min, lon_max = climate_data[lon_name].min().values, climate_data[lon_name].max().values
    lat_min, lat_max = climate_data[lat_name].min().values, climate_data[lat_name].max().values
        
    # Calculate vmin and vmax for colorbar
    vmin = climate_data.min().values  # minimum temperature value
    vmax = climate_data.max().values  # maximum temperature value
    
    fig = plt.figure(figsize=(12, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([lon_min - 2, lon_max + 2, lat_min - 1, lat_max + 1], crs=ccrs.PlateCarree())  # Adjust the extent

    ax.add_feature(cfeature.LAND, edgecolor='black', facecolor='lightgray')
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    
    # Define cmap type for climate data 
    category_config = variables_config.get(category)
    variable_config = next((item for item in category_config if item["name"] == name), None)
    cmap = variable_config["cmap"]

    heatmap = ax.pcolormesh(climate_data[lon_name], climate_data[lat_name], climate_data.isel(time=0),
                            cmap=cmap, vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())
    cbar = plt.colorbar(heatmap, ax=ax, orientation='horizontal', pad=0.05, extend='both')
    cbar.set_label(f'{category} [{units}]')
    ax.set_title(f'{category} Animation', fontsize=16)
    

    

    # Initialize the plot elements
    mesh = ax.pcolormesh(climate_data[lon_name], climate_data[lat_name], climate_data.isel(time=0),
                         cmap=cmap, transform=ccrs.PlateCarree())
    location_name = updated_query["request"]["location_name"]
    # Function to update the plot for each frame of the animation
    def update(frame):
        # Update the properties of the existing plot elements
        mesh.set_array(climate_data.isel(time=frame).values.flatten())
        date_str = np.datetime_as_string(climate_data.time[frame].values, unit="D")
        ax.set_title(f'{category} on {date_str} in {location_name}', fontsize=16)

        return mesh,

    # Create the animation
    animation = FuncAnimation(fig, update, frames=len(climate_data.time), interval=200, blit=True)
    output_path = 'ERA_DATA/results/animation.mp4'
    # Display the animation
    animation.save(output_path, writer='ffmpeg', fps=4 )
    plt.close()  # Close initial plot to prevent duplicate display

def separate_components(data: List[str]) -> List[str]:
    """
    Separate components in the list elements if they contain two components separated by a comma,
    otherwise return the list as is.
    
    Args:
        data (List[str]): Input list where some elements may contain two components separated by a comma.
    
    Returns:
        List[str]: Modified list with separated components if applicable.
    """
    modified_data = []
    
    for value in data:
        # Check if the value contains a comma
        if ',' in value:
            # Split the value into components
            components = [comp.strip() for comp in value.split(',')]
            # Extend the modified list with individual components
            modified_data.extend(components)
        else:
            modified_data.append(value)
    
    return modified_data

def process_request(request):
    """
    Process the 'product_type' key in the request dictionary.
    If the value contains two apostrophes at the start and end,
    transform it to have single quotes on the outside only.

    Args:
        request (dict): Input dictionary containing the request information.

    Returns:
        dict: Modified request dictionary with adjusted 'product_type' if applicable.
    """
    if 'variable' in request:
        variable_type = request['variable']
        # Check if the value starts and ends with two apostrophes
        if variable_type.startswith('"') and variable_type.endswith('"'):
            # Remove the double apostrophes at the start and end
            variable_type = variable_type[1:-1]
        
        # Update the request dictionary with the adjusted product_type
        request['variable'] = variable_type
    
    return request

def extract_components(lst):
    """
    Extract the content from the string inside a list and ensure it retains the inner single quotes.

    Args:
        lst (list): A list containing a single string.

    Returns:
        str: The extracted string retaining the inner single quotes.
    """
    if len(lst) == 1:
        content = lst[0]
        # Remove the leading and trailing single quotes if they exist
        if content.startswith("'") and content.endswith("'"):
            content = content[1:-1]
        return content
    else:
        raise ValueError("The list should contain exactly one string element.")

def convert_to_variable_names(names_list: List[str], variables_config: Dict[str, List[Dict[str, Any]]]) -> List[str]:
    # Initialize an empty list to store the converted variable names
    variable_names = []

    # Loop through each name in the names list
    for name in names_list:
        found = False
        # Loop through each category in the variables config
        for category, variables in variables_config.items():
            # Loop through each variable in the category
            for variable in variables:
                # Check if the name matches
                if variable['name'] == name:
                    # Append the variable_name to the result list
                    variable_names.append(variable['variable_name'])
                    found = True
                    break
            if found:
                break
    
    variable_names = separate_components(variable_names)

    return variable_names

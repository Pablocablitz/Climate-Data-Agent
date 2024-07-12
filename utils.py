import numpy as np
import yaml
from loguru import logger
from matplotlib import pyplot as plt
import re 
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.animation import FuncAnimation
import googlemaps
from typing import Dict, List, Any
import uuid 
import matplotlib.image as mpimg

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

def get_coordinates(location: str, api_key: str, min_size: float = 10) -> dict:
    """Get a bounding box for a location using Google Maps Geocoding API with a minimum size."""
    gmaps = googlemaps.Client(key=api_key)
    
    # Get place details
    geocode_result = gmaps.geocode(location)
    
    if geocode_result:
        viewport = geocode_result[0]['geometry']['viewport']
        original_bounding_box = {
            "north": viewport['northeast']['lat'],
            "south": viewport['southwest']['lat'],
            "east": viewport['northeast']['lng'],
            "west": viewport['southwest']['lng']
        }
        
        # Calculate the initial size of the bounding box
        north = original_bounding_box["north"]
        south = original_bounding_box["south"]
        east = original_bounding_box["east"]
        west = original_bounding_box["west"]

        lat_diff = north - south
        lng_diff = east - west
        
        # Ensure the bounding box has a minimum size
        if lat_diff < min_size:
            mid_lat = (north + south) / 2
            north = mid_lat + (min_size / 2)
            south = mid_lat - (min_size / 2)

        if lng_diff < min_size:
            mid_lng = (east + west) / 2
            east = mid_lng + (min_size / 2)
            west = mid_lng - (min_size / 2)
            
        adjusted_bounding_box = {"north": north, "west": west, "south": south, "east": east}


        return {
            "original_bounding_box": original_bounding_box,
            "adjusted_bounding_box": adjusted_bounding_box
        }
    else:
        return None
    
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
    ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())  # Adjust the extent

    ax.add_feature(cfeature.LAND, edgecolor='black', facecolor='lightgray')
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)
    
    # Define cmap type for climate data 
    category_config = variables_config.get(category)
    variable_config = next((item for item in category_config if item["name"] == name), None)
    cmap = variable_config["cmap"]

    heatmap = ax.pcolormesh(climate_data[lon_name], climate_data[lat_name], climate_data.isel(time=0).values.squeeze(),
                            cmap=cmap, vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())
    cbar = plt.colorbar(heatmap, ax=ax, orientation='horizontal', pad=0.05, extend='both')
    cbar.set_label(f'{category} [{units}]')
    ax.set_title(f'{category} Animation', fontsize=16)
    
    try:
        # Load the location marker icon image (replace with your own image path)
        icon_img = mpimg.imread('ERA_DATA/config_data/map.png')  # Adjust the path as needed
        
        # Example location coordinates (replace with your desired coordinates)
        location_lon = lon_min + (lon_max - lon_min) * 0.5
        location_lat = lat_min + (lat_max - lat_min) * 0.5

        # Place the icon image on the map
        ax.imshow(icon_img, extent=[location_lon - 0.3, location_lon + 0.3, location_lat - 0.3, location_lat + 0.3],
                transform=ccrs.PlateCarree(), zorder=10)
    except Exception as e:
        logger.error(f"Error getting icon: {e}")
        return {}

    # Initialize the plot elements
    mesh = ax.pcolormesh(climate_data[lon_name], climate_data[lat_name], climate_data.isel(time=0).values.squeeze(),
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
    animation_uuid = uuid.uuid4()
    output_path = f'ERA_DATA/results/animation_{animation_uuid}.mp4'    # Display the animation
    animation.save(output_path, writer='ffmpeg', fps=4 )
    plt.close()  # Close initial plot to prevent duplicate display
    
    return output_path

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

def update_non_none_values(original_dict: dict, new_dict: dict):
    """
    Update original_dict with values from new_dict, but only if the values in new_dict are not 'None'.
    
    Args:
    original_dict (dict): The original dictionary to be updated.
    new_dict (dict): The dictionary with new values.
    
    Returns:
    dict: The updated dictionary.
    """
    for key, value in new_dict.items():
        if value != 'None':
            original_dict[key] = value
    return original_dict

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

def find_coord_name(coord_names, pattern):
    """
    Function to find coordinate names using regex

    """
    for name in coord_names:
        if pattern.search(name):
            return name
    return None

def generate_descriptions(date_type, means, units):
    """
    Generate descriptions for mean values with their corresponding units.
    
    Parameters:
        date_type (list of int): List of years + month.
        annual_means (list of float): List of mean values corresponding to each year + month.
        units (str): The units of the mean values.
    
    Returns:
        dict: A dictionary with years + months as keys and descriptions as values.
    """
    descriptions = {}
    for year, mean in zip(date_type, means):
        descriptions[year] = f"{mean:.2f} {units}"
    return descriptions

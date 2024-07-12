import cdsapi
import xarray as xr
import numpy as np
from loguru import logger
from typing import Dict, List, Any
from utils import get_coordinates

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
            
    def update_request(self, data: Dict[str, Any], variables: List[str]) -> Dict[str, Any]:        
        """
        Update the request in the configuration file.
        """
        query = self.config["cds_request"]
        query["request"]["location_name"] = data["location"]
        query["request"]["start_year"] = data["start_year"]
        query["request"]["end_year"] = data["end_year"]
        query["request"]["variable"] = variables
        return query
        

    def get_data(self, query: Dict[str, Any]) -> Dict[str, Any]:
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
        area_info = get_coordinates(query["request"]["location_name"], key)
        
        if area_info is None:
            # Handle the case where get_coordinates returns None (or some other invalid value)
            logger.error(f"Failed to retrieve area coordinates for location: {query['request']['location_name']}")
            return {}  # Or raise an appropriate exception based on your error handling strategy

        self.original_area = area_info["original_bounding_box"]
        
        area = area_info["adjusted_bounding_box"]
        
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
    
    def calculate_monthly_means(self, ds, variable_name, category):
        """
        Calculate monthly mean values for a specified variable from the processed dataset.
        
        Parameters:
            ds (xarray.Dataset): The processed dataset.
            variable_name (str): The name of the variable to calculate the mean for.

        Returns:
            months (list): List of months (formatted as 'YYYY-MM').
            monthly_means (list): List of monthly mean values.
        """
        obbox = self.original_area
        
        north = obbox['north']
        south = obbox['south']
        east = obbox['east']
        west = obbox['west']

        # Filter the dataset for the original bounding box
        ds_filtered = ds.sel(latitude=slice(south, north), longitude=slice(west, east))
        
        if ds_filtered['latitude'].size == 0 or ds_filtered['longitude'].size == 0:
            logger.warning("Filtered dataset is empty using the exact original bounding box. Trying to include nearest points.")

            # Get the nearest latitude and longitude points
            nearest_lat = ds['latitude'].sel(latitude=[south, north], method='nearest')
            nearest_lon = ds['longitude'].sel(longitude=[west, east], method='nearest')

            # Perform the nearest neighbor selection
            ds_filtered = ds.sel(latitude=nearest_lat, longitude=nearest_lon)
            # Check dimensions of t2m
            logger.debug(f"Nearest point filtered dataset dimensions: {ds_filtered.dims}")
            logger.debug(f"Nearest point filtered dataset latitude range: {ds_filtered['latitude'].min().item()} to {ds_filtered['latitude'].max().item()}")
            logger.debug(f"Nearest point filtered dataset longitude range: {ds_filtered['longitude'].min().item()} to {ds_filtered['longitude'].max().item()}")
                        
        # Extract year and month from time coordinates for labeling
        months = ds_filtered['time'].dt.strftime('%Y-%m').values
      
        return months, monthly_means

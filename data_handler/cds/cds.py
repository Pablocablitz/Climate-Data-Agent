from tkinter import N
import cdsapi
from loguru import logger
from cda_classes.eorequest import EORequest
from geopy.geocoders import Nominatim
import random
import string
from datetime import datetime
from utils.utils import Utilities
import xarray as xr
import numpy as np
import pathlib


class ClimateDataStorageHandler():
    def __init__(self):

        self.client = cdsapi.Client()
        logger.info("Successfully log to Climate Data Store")
        self.load_request_format()
        self.years = []
        
    def construct_request(self, eo_request: EORequest):
        
        self.cds_request_format = self.request_format["cds_request"]["request"]
        self.location = eo_request.location
        self.timeframe = eo_request.timeframe
        self.product = eo_request.product
        self.specific_product = eo_request.specific_product
        
        self.variables = eo_request.variables
        
        self.get_coordinates_from_location()
        self.get_variable_attributes()
        self.extract_years_from_dates()
        
        self.cds_request_format["variable"] = self.variable
        self.cds_request_format["year"] = self.years
        self.cds_request_format["area"] = self.adjusted_bounding_box
        self.datatype = self.cds_request_format["format"]
        
    def get_data(self):
        request = self.cds_request_format
        name = self.request_format["cds_request"]["name"]
        self.result = self.client.retrieve(name, request)
    
    def download(self, filename):
        """
        """
        self.filename = f"{filename}.{self.datatype}"
        self.result.download(self.filename)
    
    def process(self):
        """
        Process the downloaded data.
        
        Returns:
            ds (xarray.Dataset): The processed dataset.
        """
        
        if self.datatype == "netcdf":
            ds = xr.open_dataset(self.filename, engine='netcdf4')
        elif self.datatype == "grib":
            ds = xr.open_dataset(self.filename, engine="cfgrib")
        else:
            raise ValueError(f"Unsupported format: {self.datatype}")

        if 'v10' in ds and 'u10' in ds:
            # Compute 'w10' as the magnitude of (u10, v10)
            w10 = np.sqrt(ds['u10']**2 + ds['v10']**2)
            
            # Add 'w10' to the dataset
            ds['w10'] = w10
            
            # Remove 'v10' and 'u10' from the dataset
            ds = ds.drop_vars(['v10', 'u10'])
            # Update variable_names to include 'w10'
            self.variable_names = list(ds.data_vars)
        else:
            self.variable_names = list(ds.data_vars)

        self.ds = ds
        
    
    def calculate_monthly_means(self):
        """
        Calculate monthly mean values for a specified variable from the processed dataset.
        
        Parameters:
            ds (xarray.Dataset): The processed dataset.
            variable_name (str): The name of the variable to calculate the mean for.

        Returns:
            months (list): List of months (formatted as 'YYYY-MM').
            monthly_means (list): List of monthly mean values.
        """
        obbox = self.original_bounding_box
        
        north = obbox['north']
        south = obbox['south']
        east = obbox['east']
        west = obbox['west']

        # Filter the dataset for the original bounding box
        ds_filtered = self.ds.sel(latitude=slice(south, north), longitude=slice(west, east))
        
        if ds_filtered['latitude'].size == 0 or ds_filtered['longitude'].size == 0:
            logger.warning("Filtered dataset is empty using the exact original bounding box. Trying to include nearest points.")

            # Get the nearest latitude and longitude points
            nearest_lat = self.ds['latitude'].sel(latitude=[south, north], method='nearest')
            nearest_lon = self.ds['longitude'].sel(longitude=[west, east], method='nearest')

            # Perform the nearest neighbor selection
            ds_filtered = self.ds.sel(latitude=nearest_lat, longitude=nearest_lon)
            # Check dimensions of t2m
            logger.debug(f"Nearest point filtered dataset dimensions: {ds_filtered.dims}")
            logger.debug(f"Nearest point filtered dataset latitude range: {ds_filtered['latitude'].min().item()} to {ds_filtered['latitude'].max().item()}")
            logger.debug(f"Nearest point filtered dataset longitude range: {ds_filtered['longitude'].min().item()} to {ds_filtered['longitude'].max().item()}")
                        
        # Extract year and month from time coordinates for labeling
        self.months = ds_filtered['time'].dt.strftime('%Y-%m').values
        self.monthly_means = ds_filtered[self.variable_names].groupby('time.month').mean(dim=['latitude', 'longitude']).values

        
        
    def get_coordinates_from_location(self, min_size: float = 10) -> dict:
        """Get a bounding box for a location using Google Maps Geocoding API with a minimum size."""

        apikey = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(20))
        geolocator = Nominatim(user_agent = apikey)
        geocode_result = geolocator.geocode(self.location)
        
        if geocode_result:
            viewport = geocode_result.raw['boundingbox']
            self.original_bounding_box = {
                "north": round(float(viewport[0]), 2),
                "south": round(float(viewport[1]), 2),
                "east": round(float(viewport[2]), 2),
                "west": round(float(viewport[3]), 2)
            }
            
            # Calculate the initial size of the bounding box
            north = self.original_bounding_box["north"]
            south = self.original_bounding_box["south"]
            east = self.original_bounding_box["east"]
            west = self.original_bounding_box["west"]

            lat_diff = north - south
            lng_diff = east - west
            
            # Ensure the bounding box has a minimum size
            if lat_diff < min_size:
                mid_lat = (north + south) / 2
                north = round(mid_lat + (min_size / 2), 2)
                south = round(mid_lat - (min_size / 2), 2)

            if lng_diff < min_size:
                mid_lng = (east + west) / 2
                east = round(mid_lng + (min_size / 2), 2)
                west = round(mid_lng - (min_size / 2), 2)
                
            self.adjusted_bounding_box = [north, west, south, east]



        else:
            logger.error("Location could not be detected.")
            return None
        
    def get_variable_attributes(self):
        for product in self.variables[self.product[0]]:
            if product["name"] == self.specific_product:
                self.variable = product["variable_name"]
                self.variable_units = product["units"]
                self.variable_cmap = product["cmap"]
                self.variable_short_name = product["short_name"]
                
    def extract_years_from_dates(self):
        start_date = datetime.strptime(self.timeframe[0], '%d/%m/%Y')
        end_date = datetime.strptime(self.timeframe[1], '%d/%m/%Y')

        # One-liner to extract unique years and sort them
        self.years = sorted({str(year) for year in range(start_date.year, end_date.year + 1)})
        
    def load_request_format(self):
        self.request_format = Utilities.load_config_file(
            str(
                pathlib.Path(__file__).absolute().parent) 
                + "/../request_format.yaml")
        

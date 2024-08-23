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
        self.variable = None
        
    def construct_request(self, eo_request: EORequest):
        
        self.cds_request_format = self.request_format["cds_request"]["request"]
        self.location = eo_request.request_location
        self.timeframe = eo_request.request_timeframe
        self.product = eo_request.request_product
        self.specific_product = eo_request.request_specific_product
    

        self.variables = eo_request.variables
        
        self.extract_years_from_dates()
        self.extract_months_from_dates()
        
        self.cds_request_format["variable"] = eo_request.variable
        self.cds_request_format["year"] = self.years
        self.cds_request_format["month"] = self.months
        self.cds_request_format["area"] = eo_request.adjusted_bounding_box
        self.datatype = self.cds_request_format["data_format"]
        
    def get_data(self):
        request = self.cds_request_format
        name = self.request_format["cds_request"]["name"]
        print(request, name)
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

                
    def extract_years_from_dates(self):
        start_date = self.timeframe[0]
        end_date = self.timeframe[1]

        # One-liner to extract unique years and sort them
        self.years = sorted({str(year) for year in range(start_date.year, end_date.year + 1)})
        
    def extract_months_from_dates(self):
        start_date = self.timeframe[0]
        end_date = self.timeframe[1]
        
        self.months = sorted({str(month).zfill(2) for month in range(start_date.month, end_date.month + 1)})
        
        
    def load_request_format(self):
        self.request_format = Utilities.load_config_file(
            str(
                pathlib.Path(__file__).absolute().parent) 
                + "/../request_format.yaml")
        
    def load_variables(self):
        self.variables = Utilities.load_config_file("yaml/variables.yaml") 
        return self.variables

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
        self.requests = []
        self.variable = None
        self.processed_datasets = {}

        
    def construct_request(self, eo_request: EORequest):
        
        self.cds_request_format = self.request_format["cds_request"]["request"]
        i = 0
        for area in eo_request.adjusted_bounding_box:
            
            request = self.cds_request_format.copy()
            self.timeframe = eo_request.request_timeframe
            self.product = eo_request.request_product
            self.specific_product = eo_request.request_specific_product
            self.variables = eo_request.variables
            self.location = eo_request.request_location
            self.extract_years_from_dates(eo_request.multi_time_request)
            self.extract_months_from_dates()
            
            request["variable"] = eo_request.variable
            request["year"] = self.years
            request["month"] = self.months
            request["area"] = area
            self.datatype = self.cds_request_format["data_format"]
            self.requests.append(request)
        
    def get_data(self):
        
        # file_names = ['/home/eouser/programming/Climate-Data-Agent/ERA5_Rome.grib','/home/eouser/programming/Climate-Data-Agent/ERA5_London.grib']
        for idx, request in enumerate(self.requests):
            name = self.request_format["cds_request"]["name"]
            print(request, name)
            result = self.client.retrieve(name, request)
            file = self.download("ERA_5", self.location[idx], result)
        # file = "/home/eouser/programming/Climate-Data-Agent/ERA_5_Rome.grib"
            ds = self.process(file)
            self.processed_datasets[self.location[idx]] = ds

    
    def download(self, filename, location, result, timeframe):
        """
        """
        filename = f"{filename}_{location}.{self.datatype}"
        result.download(filename)
        
        return filename
    
    
    # TODO implement a method to process all Downloaded datasets
    def process(self, file):
        """
        Process the downloaded data.
        
        Returns:
            ds (xarray.Dataset): The processed dataset.
        """
        
        if self.datatype == "netcdf":
            ds = xr.open_dataset(file, engine='netcdf4')
        elif self.datatype == "grib":
            ds = xr.open_dataset(file, engine="cfgrib")
        else:
            raise ValueError(f"Unsupported format: {self.datatype}")

        return ds
        
                
    def extract_years_from_dates(self, multi_time_ranges):
        years = set()
        
        if multi_time_ranges:
            # Iterate over pairs of dates if multi_time_ranges is True
            for i in range(0, len(self.timeframe), 2):
                start_date = self.timeframe[i]
                end_date = self.timeframe[i+1]
                
                # Add each year in the range to the set
                for year in range(start_date.year, end_date.year + 1):
                    years.add(year)
        else:
            # Single time range case
            start_date = self.timeframe[0]
            end_date = self.timeframe[1]
            
            # Add each year in the range to the set
            for year in range(start_date.year, end_date.year + 1):
                years.add(year)
        
        # Sort years and convert to list of strings
        self.years = sorted(str(year) for year in years)
        
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

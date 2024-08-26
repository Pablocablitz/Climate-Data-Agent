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
        
    def construct_request(self, eo_request: EORequest):
        
        self.cds_request_format = self.request_format["cds_request"]["request"]
        for area in eo_request.adjusted_bounding_box:
            
            request = self.cds_request_format.copy()
            self.timeframe = eo_request.request_timeframe
            self.product = eo_request.request_product
            self.specific_product = eo_request.request_specific_product
        

            self.variables = eo_request.variables
            
            self.extract_years_from_dates(eo_request.multi_time_request)
            self.extract_months_from_dates()
            
            request["variable"] = eo_request.variable
            request["year"] = self.years
            request["month"] = self.months
            request["area"] = area
            self.datatype = self.cds_request_format["data_format"]
            self.requests.append(request)
        
    def get_data(self, filename):
        for request in self.requests:
            name = self.request_format["cds_request"]["name"]
            print(request, name)
            self.result = self.client.retrieve(name, request)
            self.download(filename)
    
    def download(self, filename):
        """
        """
        self.filename = f"{filename}.{self.datatype}"
        self.result.download(self.filename)
    
    
    # TODO implement a method to process all Downloaded datasets
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
        
                
    def extract_years_from_dates(self, multi_time_ranges):
        years = set()
        if multi_time_ranges == True:
            for i in range(0, len(self.timeframe), 2):
                start_date = datetime.strptime(self.timeframe[i], '%d/%m/%Y')
                end_date = datetime.strptime(self.timeframe[i+1], '%d/%m/%Y')
                
                # Add each year in the range to the set
                for year in range(start_date.year, end_date.year + 1):
                    years.add(year)
        else:    
            start_date = datetime.strptime(self.timeframe[0], '%d/%m/%Y')
            end_date = datetime.strptime(self.timeframe[1], '%d/%m/%Y')

        # One-liner to extract unique years and sort them
            self.years = sorted({str(year) for year in range(start_date.year, end_date.year + 1)})
        
    def extract_months_from_dates(self):
        start_date = datetime.strptime(self.timeframe[0], '%d/%m/%Y')
        end_date = datetime.strptime(self.timeframe[1], '%d/%m/%Y')
        
        self.months = sorted({str(month).zfill(2) for month in range(start_date.month, end_date.month + 1)})
        
        
    def load_request_format(self):
        self.request_format = Utilities.load_config_file(
            str(
                pathlib.Path(__file__).absolute().parent) 
                + "/../request_format.yaml")
        
    def load_variables(self):
        self.variables = Utilities.load_config_file("yaml/variables.yaml") 
        return self.variables

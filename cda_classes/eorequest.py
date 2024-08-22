from utils.utils import Utilities
from loguru import logger
from collections.abc import Iterable
import streamlit as st
import numpy as np
from geopy.geocoders import Nominatim
import random
import string
import xarray as xr
from datetime import datetime

class EORequest():
    def __init__(self):
        self.request_type = None
        self.request_location = None
        self.request_timeframe = None
        self.request_product = None
        self.request_specific_product = None
        self.request_analysis = None
        self.request_visualisation = None
        self.request_valid = False
        self.variables = None
        self.adjusted_bounding_box = None
        self.original_bounding_box = None
        self.variable = None
        self.variable_units = None
        self.variable_cmap = None
        self.variable_short_name = None
        self.variable_long_name = None

        self.data = None
        self._instance_attributes = []
        self.errors = []
        
    def post_process_request_variables(self):

        if (self.request_analysis == 'predictions'):
            self._check_timeframe_and_modify()
        
        self._get_coordinates_from_location()

    def __check_validity_of_request(self):
        self.errors = []
        
        self.request_valid = True

        # Gets all the variables of EORequest
        properties = vars(self)
        # Identify only instance attributes from all EORequest variables
        self._instance_attributes = {key: value for key, value in properties.items() if (not key.startswith("_") and key.startswith("request_"))}
        print(self._instance_attributes)
        # Iterate through them all. If iterator, get subvalue. Otherwise check directly
        for key, value in self._instance_attributes.items():
            if isinstance(value, Iterable) and not isinstance(value, str):
                for subvalue in value:
                    if not Utilities.valueisvalid(subvalue):
                        self.request_valid = False
                        logger.info("checking validity of property: " + str(subvalue))
                        self.errors.append(f"{key}")
            else:
                if not Utilities.valueisvalid(value):
                    self.request_valid = False
                    logger.info("checking validity of property: " + str(value))
                    self.errors.append(f"{key}")
                
    
    def process_request(self):
        self.__check_validity_of_request()
        if not self.errors:
            for product in self.load_variables()[self.request_product[0]]:
                if product["name"] == self.request_specific_product[0]:
                    self.variable = product["variable_name"]
                    self.variable_units = product["units"]
                    self.variable_cmap = product["cmap"]
                    self.variable_long_name = product["name"]
                    self.variable_short_name = product["short_name"]
                    self.vmin = product["vmin"]
                    self.vmax = product["vmax"]


    def construct_product_agent_instruction(self):
        product_list = [product['name'] for product in self.load_variables()[self.request_product[0]]]
        instruction_format = f"'{self.request_product[0]}':\n- {product_list}"
        return instruction_format
    
    def load_variables(self):
        return Utilities.load_config_file("yaml/variables.yaml") 
    
    def store_and_process_data(self, data):
        self.data = data

        
        self._process_data()
        
    def _process_data(self):
        variable_names = list(self.data.data_vars)
                
        match(variable_names[0]):
            case "v10":
                self._process_windspeed()
                
            case "u10":
                self._process_windspeed()
                
            case "e":
                self.data["e"] *= -1000  #convert from m to mm 
                self.variable_units = "mm"
                               
            case "t2m":
                self.data["t2m"] -= 273.15  #convert from kelvin to celsius

            case "skt":
                self.data["skt"] -= 273.15  #convert from kelvin to celsius

            case "tp":
                self.data["tp"] *= 1000 #convert m to mm in precipitation data
                self.variable_units = "mm"

            case _:
                message = "Unexpected type of variable name provided! Received:" + variable_names[0]
                logger.error(message)
                
    def _process_windspeed(self):
        """
        calculate wind speed on component vectors u and v
        """
        w10 = np.sqrt(self.data['u10']**2 + self.data['v10']**2)
        
        # Add 'w10' to the dataset
        self.data['w10'] = w10
        
        # Remove 'v10' and 'u10' from the dataset
        self.data = self.data.drop_vars(['v10', 'u10'])
        
    def _get_coordinates_from_location(self, min_size: float = 10) -> dict:
        """Get a bounding box for a location using Google Maps Geocoding API with a minimum size."""

        apikey = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(20))
        geolocator = Nominatim(user_agent = apikey)
        geocode_result = geolocator.geocode(self.request_location)
        
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
        
    def _check_timeframe_and_modify(self):
        start_date = datetime.strptime(self.timeframe[0], '%d/%m/%Y')
        date_cap = datetime.strptime("31/12/2023", '%d/%m/%Y')
        date_user = datetime.strptime(self.timeframe[1], '%d/%m/%Y')
        
        end_date = min(date_cap, date_user)
        self.request_timeframe[1] = end_date.strftime('%d/%m/%Y')
        difference = datetime.timedelta(start_date, end_date)
        
        if difference.years < 3:
            missing_years = np.ceil(3 - difference.years) * -1
            self.request_timeframe[0] = start_date.addYears(missing_years).strftime('%d/%m/%Y')
        
        
    def populate_dummy_data(self):
        self.request_type = ["True"]
        self.request_location = ["Aachen"]
        self.request_timeframe = ['01/01/2010', '31/12/2020']
        self.request_product = ["Temperature"]
        self.request_specific_product = ["2m temperature"]
        self.request_analysis = ["predictions"]
        self.request_visualisation = ["time_series"]
        self.request_valid = True
        self.adjusted_bounding_box = [55.76, 1.09, 45.76, 11.09]
        self.original_bounding_box = {"north": 51.29, "south": 51.69, "east": -0.51, "west": 0.33}
        self.variable = "2m_temperature"
        self.variable_units = "\u00b0C"
        self.variable_cmap = "balance"
        self.variable_short_name = "t2m"
        self.variable_long_name = "2m temperature"
        
        self.errors = []
        
        self.vmin = "-10"
        self.vmax = "40"
        
        self.store_and_process_data(xr.open_dataset("ERA5_prophet_training_file.grib", engine="cfgrib"))
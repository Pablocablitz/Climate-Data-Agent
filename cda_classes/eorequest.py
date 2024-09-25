import random
import string
import xarray as xr
import numpy as np
import math

from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
from utils.utils import Utilities, TimeSpan, SubRequest
from loguru import logger
from collections.abc import Iterable
from collections import defaultdict


class EORequest():
    def __init__(self):
        self.request_type = []
        self.request_locations = []
        self.request_timeframes = []
        self.request_product = None
        self.request_specific_product = None
        self.request_analysis = None
        self.request_visualisation = True 
        self.request_valid = False
        
        self.variables = None
        self.adjusted_bounding_box = []
        self.original_bounding_box = []
        self.variable = None
        self.variable_units = None
        self.variable_cmap = None
        self.variable_short_name = None
        self.variable_long_name = None
        self.multi_loc_request = False
        self.multi_time_request = False
        self.data = None
        self._instance_attributes = []
        self.errors = []
        self.user_prompt = None
        self.collected_sub_requests = []
        self.intervall_same_length = False
        self.sub_time_request = False

        
    def post_process_request_variables(self):
        
#        if self.request_timeframe[0] not in ["None", None]:       
#            for i in range(len(self.request_timeframe)):
#                self.request_timeframe[i] = self.parse_date(self.request_timeframe[i])

        if (self.request_analysis[0] == 'predictions') and self.request_timeframes != ["None"]:
            self._check_timeframe_and_modify()
            logger.info("checked for timeframe")
        
        if self.request_locations[0] not in ["None", None]:  
            for location in self.request_locations:
                try:
                    adjusted_box, original_box = self._get_coordinates_from_location(location)
                    self.adjusted_bounding_box.append(adjusted_box)
                    self.original_bounding_box.append(original_box)
                except Exception as e:  # Specify the exception to catch
                    # Handle the exception (optional: log the error message)
                    print(f"Error processing location '{location}': {e}")
                    self.request_locations = ["None"]  # Setting request_locations to None if any error occurs
                    break  # Optionally break out of the loop if an error occurs

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
    
    def store_and_process_data(self):
        if self.sub_time_request:
            self._combine_request_same_id()
            
        self._process_data()
        
    def _process_data(self):
        
        variable_names = self.variable_short_name
        for request in self.collected_sub_requests:
            match(variable_names):
                case "w10":
                    pass
                #     self._process_windspeed(request)
                    
                # case "w10":
                #     self._process_windspeed(request)
                    
                case "e":
                    request.data *= -1000  #convert from m to mm 
                    self.variable_units = "mm"
                                
                case "t2m":
                    request.data -= 273.15  #convert from kelvin to celsius

                case "skt":
                    request.data -= 273.15  #convert from kelvin to celsius

                case "tp":
                    request.data *= 1000 #convert m to mm in precipitation data
                    self.variable_units = "mm"

                case _:
                    message = "Unexpected type of variable name provided! Received:" + variable_names[0]
                    logger.error(message)
                    
    def _process_windspeed(self, request):
        """
        calculate wind speed on component vectors u and v
        """
        w10 = np.sqrt(request.data['u10']**2 + request.data['v10']**2)
        
        # Add 'w10' to the dataset
        request.data['w10'] = w10
        
        # Remove 'v10' and 'u10' from the dataset
        request.data = request.data.drop_vars(['v10', 'u10'])
        
    def _get_coordinates_from_location(self,request_location, min_size: float = 3) -> dict:
        """Get a bounding box for a location using Google Maps Geocoding API with a minimum size."""

        apikey = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(20))
        geolocator = Nominatim(user_agent = apikey)
        geocode_result = geolocator.geocode(request_location)
        
        if geocode_result:
            viewport = geocode_result.raw['boundingbox']
            original_bounding_box = {
                "north": round(float(viewport[0]), 2),
                "south": round(float(viewport[1]), 2),
                "east": round(float(viewport[2]), 2),
                "west": round(float(viewport[3]), 2)
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
                north = round(mid_lat + (min_size / 2), 2)
                south = round(mid_lat - (min_size / 2), 2)

            if lng_diff < min_size:
                mid_lng = (east + west) / 2
                east = round(mid_lng + (min_size / 2), 2)
                west = round(mid_lng - (min_size / 2), 2)
                
            adjusted_bounding_box = [north, west, south, east]

            return adjusted_bounding_box, original_bounding_box


        else:
            logger.error("Location could not be detected.")
            return None
       
    def _check_timeframe_and_modify(self):
        for timeframe in self.request_timeframes:
            
            start_date = timeframe.startdate
            enddate_user = timeframe.enddate
            timeframe.prediction_startdate = timeframe.startdate
            timeframe.prediction_enddate = timeframe.enddate
            
            # Calculate the prediction difference in years
            prediction_diff = (enddate_user - start_date).days - 2
            prediction_diff_years = prediction_diff/365.25
            timeframe.prediction_number = math.ceil(prediction_diff_years)
            
            # Cap the end date to a maximum of 31/12/2023
            date_cap = datetime.strptime("31/12/2023", '%d/%m/%Y')
            end_date = min(date_cap, enddate_user)
            
            # Always set start date to be 3 years before the end date
            start_date = datetime.strptime("01/01/2021", '%d/%m/%Y')  # Adjust for leap years

            # Update the timeframe with the new start and end dates
            timeframe.startdate = start_date
            timeframe.enddate = end_date
            timeframe.startdate_str = start_date.strftime("%d/%m/%Y")
            timeframe.enddate_str = end_date.strftime("%d/%m/%Y")


            
            print(timeframe.startdate, timeframe.enddate)
            
                            
    def populate_dummy_data(self):
        self.request_type = ["True"]
        self.request_locations = ["Aachen"]
        self.request_timeframe = TimeSpan(['01/01/2010', '31/12/2020'])
        self.request_timeframe.startdate = datetime.strptime("01/01/2010", '%d/%m/%Y')
        self.request_timeframe.enddate = datetime.strptime("31/12/2020", '%d/%m/%Y')

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
    
    def process_and_store_timeframe(self, timelist):
        if timelist not in ["None", None]:  
            for i in range(0, len(timelist), 2):
                self.request_timeframes.append(TimeSpan(timelist[i], timelist[i+1]))
                
    def collect_eorequests(self):
        print(f'timeframe objects {self.request_timeframes}')
        id_request = 0
        for idx, location in enumerate(self.request_locations):
            
            for timeframe in self.request_timeframes:
                
                # Calculate the duration
                months = (timeframe.enddate.month - timeframe.startdate.month)
                

                            # Check if the duration is less than one year
                if months < 11:
                    self.sub_time_request = True
                    current_date = timeframe.startdate
                    while current_date <= timeframe.enddate:
                        # Calculate the next year
                        next_year = current_date.year + 1
                        
                        # Determine the end date for the current year segment
                        if next_year > timeframe.enddate.year:
                            year_end_date = timeframe.enddate  # Last segment is capped by the overall end date
                        else:
                            year_end_date = datetime(next_year, 1, 1) - timedelta(days=1)  # Last day of the current year
                            
                                    # Create SubSubRequest for the time span from current_date to year_end_date
                        subrequest = SubRequest(
                            location,
                            self.original_bounding_box[idx],
                            self.adjusted_bounding_box[idx],
                            TimeSpan(current_date, year_end_date),
                            self.variable_short_name,
                            id_request
                        )
                        self.collected_sub_requests.append(subrequest)
                        
                        # Move to the first day of the next year
                        current_date = year_end_date + timedelta(days=1)
                        
                    id_request +=1
                    
                    self.sub_time_request = True
                    
                else:
                    sub_request = SubRequest(location, self.original_bounding_box[idx], self.adjusted_bounding_box[idx], timeframe, self.variable_short_name, id_request)
                    print(f'Created SubRequest without SubSubRequests: {sub_request}')
                    id_request +=1
                    self.collected_sub_requests.append(sub_request)
                
                
    def append_data_to_requests(self, data_list):
        for idx, data in enumerate(data_list):
            if idx < len(self.collected_sub_requests):
                self.collected_sub_requests[idx].append_request_data(data)
                
    def _combine_request_same_id(self):
        # Group requests by id_request
        grouped_subrequests = defaultdict(list)
        
        for subrequest in self.collected_sub_requests:
            grouped_subrequests[subrequest.id_request].append(subrequest)
        
        new_collected_sub_requests = []

        
        for id_request, subrequests in grouped_subrequests.items():
            merged_subrequest = self.merge_data_of_all_subrequests_with_same_id(id_request, subrequests) 
            new_collected_sub_requests.append(merged_subrequest)
            
        self.collected_sub_requests.clear()
        self.collected_sub_requests.extend(new_collected_sub_requests)

        return grouped_subrequests

    def merge_data_of_all_subrequests_with_same_id(self, id_request, subrequests):
        # Assuming that `data` is just a placeholder for actual data, we'll concatenate it.
        # Modify this function based on the actual structure of `data`.
        merged_data = []

        
        for subrequest in subrequests:
            if subrequest.data is not None and subrequest.data.size > 0:
                merged_data.append(subrequest.data)  # Replace this with the actual data merging logic
                
        merged_time_frame = TimeSpan(subrequests[0].timeframe_object.startdate_str, subrequests[-1].timeframe_object.enddate_str)
        concatenated_data = xr.concat(merged_data, dim='time')
        
        # Create a new SubRequest with the merged data and timeframe
        merged_request = SubRequest(subrequests[0].location,                             
                                    subrequests[0].obbox,
                                    subrequests[0].abbox,
                                    merged_time_frame, 
                                    subrequests[0].variable_shortname,
                                    id_request
                                    )
        merged_request.append_request_data(concatenated_data)  # Assuming data is merged here
        
        return merged_request
                

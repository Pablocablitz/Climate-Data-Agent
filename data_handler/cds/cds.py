import cdsapi
import xarray as xr
import pathlib
import numpy as np

from utils.utils import Utilities
from cda_classes.eorequest import EORequest
from loguru import logger
from datetime import timedelta
from utils.utils import apply_timing_decorator

# Class to process the request of the User when he is asking for CDS Data
@apply_timing_decorator
class ClimateDataStorageHandler():
    def __init__(self):

        self.client = cdsapi.Client()
        logger.info("Successfully log to Climate Data Store")
        self.load_request_format()
        self.years = []
        self.requests = []
        self.variable = None
        self.days = []
        self.months = []
        

        
    def construct_request(self, eo_request: EORequest):
        
        self.cds_request_format = self.request_format["cds_request"]["request"]
        
        for sub_request in eo_request.collected_sub_requests:
            
            request = self.cds_request_format.copy()

            self.timeframe = sub_request.timeframe_object.time_range
            self.product = eo_request.request_product
            self.specific_product = eo_request.request_specific_product
            self.variables = eo_request.variables
            self.location = sub_request.location
            self.extract_years_from_dates(sub_request.timeframe_object, eo_request.multi_time_request)
            self.extract_months_from_dates(sub_request.timeframe_object)
            self.extract_days_from_dates(sub_request.timeframe_object)
            request["variable"] = eo_request.variable
            request["year"] = self.years
            request["month"] = self.months
            request['days'] = self.days
            request["area"] = sub_request.abbox
            self.datatype = self.cds_request_format["data_format"]
            self.requests.append(request)

    def get_data(self, collected_sub_requests):
        
        # file_names = ['/home/eouser/programming/Climate-Data-Agent/ERA5_Rome.grib','/home/eouser/programming/Climate-Data-Agent/ERA5_London.grib']
        for sub_request, request in zip(collected_sub_requests, self.requests):
            name = self.request_format["cds_request"]["name"]
            print(request, name)
            result = self.client.retrieve(name, request)
            file = self.download("ERA_5", self.location, result)
            ds = self.process(file)
            if sub_request.variable_shortname == 'w10':
                ds_opened = self._process_windspeed(ds)
            else:
                ds_opened = ds[sub_request.variable_shortname]
            sub_request.append_request_data(ds_opened)

    
    def download(self, filename, location, result):
        """
        """
        filename = f"{filename}_{location}.{self.datatype}"
        result.download(filename)
        
        return filename
    
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
        
    def extract_years_from_dates(self,timeframe_object, multi_time_ranges):
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
            start_date = timeframe_object.startdate
            end_date = timeframe_object.enddate
            
            # Add each year in the range to the set
            for year in range(start_date.year, end_date.year + 1):
                years.add(year)
        
        # Sort years and convert to list of strings
        self.years = sorted(str(year) for year in years)
        
    def extract_days_from_dates(self, timeframe_object):
        start_date = timeframe_object.startdate
        end_date =timeframe_object.enddate
        
        # Create a set to store unique days
        days_set = set()

        # Loop through the range of dates and add the days to the set
        current_date = start_date
        while current_date <= end_date:
            days_set.add(f"{current_date.day:02}")  # Format day as two digits using f-string
            current_date += timedelta(days=1)  # Move to the next day

        # Convert the set to a sorted list of unique days
        self.days = sorted(days_set)
        
    def extract_months_from_dates(self, timeframe_object):
        start_date = timeframe_object.startdate
        end_date = timeframe_object.enddate
        
        self.months = sorted({str(month).zfill(2) for month in range(start_date.month, end_date.month + 1)})
        
        
    def load_request_format(self):
        self.request_format = Utilities.load_config_file(
            str(
                pathlib.Path(__file__).absolute().parent) 
                + "/../request_format.yaml")
        
    def load_variables(self):
        self.variables = Utilities.load_config_file("yaml/variables.yaml") 
        return self.variables
    
    def generate_cdsapi_code(self,eo_request:EORequest, dataset, variable, year, month, day, time, data_format, download_format, area):
        
        code = f"""
                    import cdsapi

                    dataset = "{self.request_format["cds_request"]['name']}"
                    request = {{
                        'variable': {eo_request.variable},
                        'year': {self.years},
                        'month': {self.months},
                        'day': {self.cds_request_format['day']},
                        'time': {self.cds_request_format['time']},
                        'data_format': '{self.cds_request_format['data_format']}',
                        'download_format': '{self.cds_request_format['download_format']}',
                        'area': {eo_request.collected_eorequests.abbox}
                    }}

                    client = cdsapi.Client()
                    client.retrieve(dataset, request).download()
                """
        return code
    
    def _process_windspeed(self, ds):
        """
        calculate wind speed on component vectors u and v
        """
        w10 = np.sqrt(ds['u10']**2 + ds['v10']**2)
        
        # Add 'w10' to the dataset
        ds['w10'] = w10
        
        # Remove 'v10' and 'u10' from the dataset
        ds = ds.drop_vars(['v10', 'u10'])
        
        ds_opened = ds['w10']
        
        return ds_opened

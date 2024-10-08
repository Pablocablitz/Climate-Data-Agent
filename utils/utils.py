import yaml 
import json 
import numpy as np
import time 
import functools
import csv
import os

from loguru import logger
from datetime import datetime

class Utilities():
    
    @staticmethod
    def load_config_file(file_path: str) -> dict:
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

    @staticmethod
    def cleaned_dict_output(response: str) -> dict:
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
            logger.error("No JSON object found in the response.")
            return None
        
        # Extract the JSON string
        json_str = response[start_idx:end_idx + 1]
        
        # Replace single quotes with double quotes for valid JSON
        json_str = json_str.replace("'", '"')
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return None
        
        
    @staticmethod
    def valueisvalid(value):
        valueisvalid = True
        if (value == "None" or value == None or not value):
            valueisvalid = False        
        return valueisvalid
    
    @staticmethod
    def significant_round(x, p):
        x_positive = np.where(np.isfinite(x) & (x != 0), np.abs(x), 10**(p-1))
        mags = 10 ** (p - 1 - np.floor(np.log10(x_positive)))
        return np.round(x * mags) / mags
    
    @staticmethod    
    def parse_date(date_str):
        """Parse date from various formats including:
        - 'dd/mm/yyyy', 'dd-mm-yyyy', 'dd.mm.yyyy'
        - 'yyyy/mm/dd', 'yyyy-mm-dd', 'yyyy.mm.dd'
        - 'mm/dd/yyyy', 'mm-dd-yyyy', 'mm.dd.yyyy' (US format)
        - 'dd MMM yyyy' (e.g., '16 Sep 2023')
        - 'dd Month yyyy' (e.g., '16 September 2023')
        - 'yyyy MM dd', 'yyyy Month dd' (ISO-like)
        """
        # Define potential date formats to try
        date_formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', 
            '%Y-%m-%d','%d.%m.%Y', '%Y.%m.%d',           
            '%m/%d/%Y', '%m-%d-%Y', '%m.%d.%Y',           
            '%d %b %Y', '%d %B %Y','%Y %b %d',                      
                '%Y %B %d', '%d %m %Y', '%Y %m %d',                     
            '%b %d, %Y', '%B %d, %Y'                   
        ]
        
        # Try each format in sequence
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # None of the formats matched
        raise ValueError(f"Date format of '{date_str}' is not recognized")
    
    @staticmethod     
    def join_locations(locations):
        if not locations:
            return ""
        
        if len(locations) == 1:
            return locations[0]
        
        # Join all but the last location with commas
        return ", ".join(locations[:-1]) + ", and " + locations[-1]
    

class TimeSpan():
    def __init__(self, startdate, enddate):
        self.prediction_number = None
        self.prediction_startdate = None
        self.prediction_enddate = None
        if (isinstance(startdate, str)):
            self.startdate = Utilities.parse_date(startdate)
            self.startdate_str = self.startdate.strftime("%d/%m/%Y")
            self.enddate = Utilities.parse_date(enddate)
            self.enddate_str = self.enddate.strftime("%d/%m/%Y")
            self.time_range = [self.startdate, self.enddate]
            
        elif (isinstance(startdate, datetime)):
            self.startdate = startdate
            self.enddate = enddate
            self.startdate_str = self.startdate.strftime("%d/%m/%Y")
            self.enddate_str = self.enddate.strftime("%d/%m/%Y")
            self.time_range = [self.startdate, self.enddate]
            
class SubRequest():
    def __init__(self, location, obbox, abbox, timeframe_object, variable_shortname, id_request):
        self.location = location
        self.obbox = obbox
        self.abbox = abbox 
        self.timeframe_object = timeframe_object
        self.data = None
        self.variable_shortname = variable_shortname
        self.prediction_number = None
        self.id_request = id_request
    def append_request_data(self, data):
        self.data = data
    
    def append_prediction_years(self, number):
        self.prediction_number = number
        
def time_function(log_file='timing_log.txt'):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine the class name if the function is a method
            cls_name = ''
            if args:
                cls = args[0].__class__
                if hasattr(cls, func.__name__):
                    cls_name = cls.__name__ + '.'
        
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            log_message = f"Function '{cls_name}{func.__name__}' executed in {execution_time:.6f} seconds\n"
            with open(log_file, 'a') as f:
                f.write(log_message)
            return result
        return wrapper
    return decorator

def time_function_csv(csv_file='timing_log.csv'):
    # Ensure the CSV file has headers if it doesn't exist
    if not os.path.isfile(csv_file):
        with open(csv_file, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Function Name', 'Execution Time (s)'])

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Skip logging for the __init__ method
            if func.__name__ == '__init__':
                return func(*args, **kwargs)

            cls_name = ''
            if args:
                cls = args[0].__class__
                if hasattr(cls, func.__name__):
                    cls_name = cls.__name__ + '.'

            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Log to CSV
            log_entry = [f"{cls_name}{func.__name__}", execution_time]
            with open(csv_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(log_entry)
                
            return result
        return wrapper
    return decorator

def apply_timing_decorator(cls, log_file='timing_log.csv'):
    for attr_name, attr_value in cls.__dict__.items():
        if callable(attr_value):
            setattr(cls, attr_name, time_function_csv(log_file)(attr_value))
    return cls

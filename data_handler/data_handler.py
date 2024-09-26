import os
import cfgrib
import xarray as xr
import numpy as np

from data_handler.cds import ClimateDataStorageHandler
from cda_classes.eorequest import EORequest
from utils.utils import apply_timing_decorator


@apply_timing_decorator
class DataHandler():
    def __init__(self, ):
        self.request_cds = ClimateDataStorageHandler()
        # self.cds = ClimateDataStorageHandler(self.request)
        self.data_available_in_db = False
        self.processed_datasets = {}
    def construct_request(self, eo_request: EORequest):
        # if (eo_request.datasource == "CDS"):
        self.request_cds.construct_request(eo_request)
        
        

    def construct_multi_request(self, eo_request: EORequest):
        
        # if (eo_request.datasource == "CDS"):
        pass    
    

    def download(self,  eo_request: EORequest):
        
        self.construct_request(eo_request)
        self.check_for_data_in_database(eo_request)
        if not self.data_available_in_db:
            self.request_cds.get_data(eo_request.collected_sub_requests)
            
            

        
    def check_for_data_in_database(self, eo_request):
        self.data_available_in_db = True
        grib_folder = '/my_volume/cds_data/ERA_5_LAND_2000_2024'
        
        for sub_request, request in zip(eo_request.collected_sub_requests, self.request_cds.requests):
            target_years = request['year']
            target_months = request['month']
            target_area = request['area']
            if eo_request.variable_short_name == 'w10':
                target_variable = 'u10'
            else:    
                target_variable = eo_request.variable_short_name

            # Get all files in the grib folder
            files_in_folder = [f for f in os.listdir(grib_folder) if f.endswith('.grib')]

            # Filter files by target years and months
            filtered_files = [
                f for f in files_in_folder 
                if any(f.startswith(f"{int(year)}_{int(month):02d}") for year in target_years for month in target_months)
            ]

            # Sort the filenames for consistency
            filtered_files.sort()

            datasets = []  # To concatenate the months to one xarray dataset

            # Loop through filtered files and process them
            for filename in filtered_files:
                grib_file_path = os.path.join(grib_folder, filename)

                # Open the GRIB file using cfgrib
                ds_list = cfgrib.open_datasets(grib_file_path)
                
                # Loop through datasets and filter by the target variable and area
                for i, dataset in enumerate(ds_list):
                    if target_variable in dataset.data_vars:
                        try:
                            if target_variable == 'u10':
                                ds_filtered = self._process_windspeed_of_db(dataset, target_area)
                            else:
                                ds_filtered = dataset[target_variable].sel(
                                    latitude=slice(target_area[0], target_area[2]), 
                                    longitude=slice(target_area[1], target_area[3])
                                )
                            datasets.append(ds_filtered)
                        except Exception as e:
                            print(f"Error processing dataset: {e}")
                            self.data_available_in_db = False

            # Concatenate all the datasets once after loading them
            if datasets:
                ds_database = xr.concat(datasets, dim='time')
                ds_sorted = ds_database.sortby('time')  # Sort by the time coordinate

                # Check if the dataset is empty by checking the size or any of the dimensions
                if ds_sorted.size == 0:
                    self.data_available_in_db = False
                else:
                    # Save the sorted dataset in the processed datasets dictionary
                    sub_request.append_request_data(ds_sorted)
            else:
                self.data_available_in_db = False
                
    def _process_windspeed_of_db(self, ds, target_area):
        ds_sliced = ds.sel(
                        latitude=slice(target_area[0], target_area[2]), 
                        longitude=slice(target_area[1], target_area[3])
                    )
        w10 = np.sqrt(ds_sliced['u10']**2 + ds_sliced['v10']**2)
        
        # Add 'w10' to the dataset
        ds_sliced['w10'] = w10
        
        # Remove 'v10' and 'u10' from the dataset
        ds = ds_sliced.drop_vars(['v10', 'u10'])
        
        ds_opened = ds['w10']
        return ds_opened
        
                                    
                                
            
        


from data_handler.cds import ClimateDataStorageHandler
from cda_classes.eorequest import EORequest
from loguru import logger
import numpy as np
import os
import cfgrib
import xarray as xr

class DataHandler():
    def __init__(self, ):
        self.request_cds = ClimateDataStorageHandler()
        # self.cds = ClimateDataStorageHandler(self.request)
        self.data_unavailable_in_db = False
        self.processed_datasets = {}
    def construct_request(self, eo_request: EORequest):
        # if (eo_request.datasource == "CDS"):
        self.request_cds.construct_request(eo_request)
        
        

    def construct_multi_request(self, eo_request: EORequest):
        
        # if (eo_request.datasource == "CDS"):
        pass    
    

    def download(self,  eo_request: EORequest):
        self.__check_for_data_in_database(eo_request)
        if self.data_unavailable_in_db:
            cds_datasets = self.request_cds.get_data(self.processed_datasets)
            # self.request_cds.process()
            self.data = cds_datasets
            
        else:
            print(self.processed_datasets)
            self.data = self.processed_datasets
            # if (eo_request.datasource == "CDS"):
            #     self.cds.download()
        
    def __check_for_data_in_database(self, eo_request):
        grib_folder = '/my_volume/cds_data/ERA_5_LAND_2000_2024'
        
        for idx, request in enumerate(self.request_cds.requests):
            target_years = request['year']
            target_months = request['month']
            target_area = request['area']
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
                year, month = filename.split('_')[:2]  # Extract year and month
                grib_file_path = os.path.join(grib_folder, filename)

                # Open the GRIB file using cfgrib
                ds_list = cfgrib.open_datasets(grib_file_path)
                
                # Loop through datasets and filter by the target variable and area
                for i, dataset in enumerate(ds_list):
                    if target_variable in dataset.data_vars:
                        try:
                            ds_filtered = dataset[target_variable].sel(
                                latitude=slice(target_area[0], target_area[2]), 
                                longitude=slice(target_area[1], target_area[3])
                            )
                            datasets.append(ds_filtered)
                        except Exception as e:
                            print(f"Error processing dataset: {e}")
                            self.data_unavailable_in_db = True

            # Concatenate all the datasets once after loading them
            if datasets:
                ds_database = xr.concat(datasets, dim='time')
                ds_sorted = ds_database.sortby('time')  # Sort by the time coordinate

                # Save the sorted dataset in the processed datasets dictionary
                self.processed_datasets[eo_request.request_location[idx]] = ds_sorted
            else:
                self.data_unavailable_in_db = True
                                    
                                
            
        


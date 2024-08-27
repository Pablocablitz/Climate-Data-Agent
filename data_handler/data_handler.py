from data_handler.cds import ClimateDataStorageHandler
from cda_classes.eorequest import EORequest
from loguru import logger
import numpy as np

class DataHandler():
    def __init__(self, ):
        self.request_cds = ClimateDataStorageHandler()
        # self.cds = ClimateDataStorageHandler(self.request)

    def construct_request(self, eo_request: EORequest):
        # if (eo_request.datasource == "CDS"):
        self.request_cds.construct_request(eo_request)

    def construct_multi_request(self, eo_request: EORequest):
        
        # if (eo_request.datasource == "CDS"):
        pass    
    

    def download(self, filename):
        self.request_cds.get_data(filename)
        # self.request_cds.process()
        self.data = self.request_cds.processed_datasets
        # if (eo_request.datasource == "CDS"):
        #     self.cds.download()


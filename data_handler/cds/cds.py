import cdsapi
from loguru import logger
from cda_classes.eorequest import EORequest

class ClimateDataStorageHandler():
    def __init__(self, request):
        try:
            self.client = cdsapi.Client()
            self.cds_request_format = request["cds_request"]
            logger.info("Successfully log to Climate Data Store")
        except:
            logger.error("Could not log to Climate Data Store")
        self.type = "CDS"
        
        
    def construct_request(self, eo_request: EORequest):
        
        self.cds_request_format["name"] = user_request[""]
        self.cds_request_format["variable"] = user_request[""]
        self.cds_request_format["time"] = user_request[""]
        self.cds_request_format["years"] = user_request[""]
        self.cds_request_format["month"] = user_request[""]
        self.cds_request_format["location_name"] = user_request[""]
        self.cds_request_format["format"] = user_request[""]
        
    def get_data(self):
        request = self.cds_request_format
        self.result = self.client.retrieve(request)
    
    def download(self, filename):
        """
        """
        self.filename = f"{filename}.{self.format}"
        self.result.download(self.filename)
        
    
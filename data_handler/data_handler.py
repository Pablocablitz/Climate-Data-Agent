from cds import ClimateDataStorageHandler
from chatbot import EORequest

class DataHandler():
    def __init__(self, ):
        self.request = load_config_dict("request_format.yaml")
        self.cds = ClimateDataStorageHandler(self.request)

    def construct_request(self, eo_request: EORequest):
        if (eo_request.datasource == "CDS"):
            self.cds.construct_request(eo_request)
        

    def download(self, eo_request):
        if (eo_request.datasource == "CDS"):
            self.cds.download()
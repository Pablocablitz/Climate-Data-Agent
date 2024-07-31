from data_handler.cds import ClimateDataStorageHandler
from cda_classes.eorequest import EORequest

class DataHandler():
    def __init__(self, ):
        self.request_cds = ClimateDataStorageHandler()
        # self.cds = ClimateDataStorageHandler(self.request)

    def construct_request(self, eo_request: EORequest):
        # if (eo_request.datasource == "CDS"):
        self.request_cds.construct_request(eo_request)


    def download(self, filename):
        self.request_cds.get_data()
        self.request_cds.download(filename)
        self.request_cds.process()

        self.data = self.request_cds.ds
        
        # if (eo_request.datasource == "CDS"):
        #     self.cds.download()

from cds import ClimateDataStorageHandler
from chatbot import EORequest

class DataHandler():
    def __init__(self):
        self.cds = ClimateDataStorageHandler()

    def construct_request(eo_request: EORequest):
        pass

    def download(self, eo_request):
        if (eo_request.datasource == "CDS"):
            self.cds.download()
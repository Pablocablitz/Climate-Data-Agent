from loguru import logger
import xarray as xr

class AnalysisHandler():
    def __init__(self):
        self.analysis_types = "basic_analysis, significant_event_detection, predictions, comparison"

    def basic_analysis(self, dataset: xr.Dataset):
        return "The highest datapoint is detected at timestamp: "
        pass

    def significant_event_detection(self, dataset: xr.Dataset):
        logger.warning("Attempted significant event detection, but this is not implemented yet!")

    def predictions(self, dataset: xr.Dataset):
        logger.warning("Attempted to perform predictions, but this is not implemented yet!")

    def comparison(self, dataset: xr.Dataset):
        logger.warning("Attempted comparison of two datasets, but this is not implemented yet!")
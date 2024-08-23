from loguru import logger
import xarray as xr
from .eorequest import EORequest
import pandas as pd
import numpy as np
import string
from utils.utils import Utilities
import plotly.express as px
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components
import plotly.graph_objs as go



class AnalysisHandler():
    def __init__(self):
        self.analysis_types = "basic_analysis, significant_event_detection, predictions, comparison"

    def basic_analysis(self, eo_request: EORequest):
        # a basic analysis contains:
        # * minima and maxima
        # * standard deviation
        
        df = self.get_monthly_mean_dataframe(eo_request)
        
        minval, maxval = self.get_min_max_from_dataframe(df)
        
        return self.get_plot_from_dataframe(df, eo_request.variable_long_name + " [" + eo_request.variable_units + "]"), self.get_basic_analysis_string(
            minval,
            maxval,
            self.get_std_from_dataframe(df),
            eo_request.variable_units
        )
        self.calculate_monthly_means(eo_request)
        return self.calculate_monthly_means(eo_request)
    
        return stringtoprint, plot

    def significant_event_detection(self, eo_request: EORequest):
        # * Outlier/Anomaly detection
        logger.warning("Attempted significant event detection, but this is not implemented yet!")

    def predictions(self, eo_request: EORequest):
        df = self._get_dataframe_from_eorequest(eo_request)
        
        model = Prophet()
        
        model.fit(df)
        
        # figure out what a period is, possibly calculate timesteps in order to ensure predicitons are always for e.g. 1 year
        future = model.make_future_dataframe(periods=1000)
        forecast = model.predict(future)
        message = "The following prediction was performed based on the downloaded data. The prediction encompasses 1000 periods [TBC]"
        
        # Create a Plotly figure
        fig = go.Figure()

        # Add the training data trace
        fig.add_trace(go.Scatter(
            x=df['ds'], 
            y=df['y'], 
            mode='lines', 
            name='Training Data',
            line=dict(color='red')  # Set the color for training data
        ))

        # Add the forecast trace
        fig.add_trace(go.Scatter(
            x=forecast['ds'], 
            y=forecast['yhat'], 
            mode='lines', 
            name='Forecast',
            line=dict(color='blue')  # Set the color for forecast data
        ))

        # Add the confidence interval (upper bound)
        fig.add_trace(go.Scatter(
            x=forecast['ds'], 
            y=forecast['yhat_upper'], 
            mode='lines', 
            name='Upper Confidence Interval',
            line=dict(width=0),  # No line, just the fill
            showlegend=False
        ))

        # Add the confidence interval (lower bound)
        fig.add_trace(go.Scatter(
            x=forecast['ds'], 
            y=forecast['yhat_lower'], 
            mode='lines', 
            name='Lower Confidence Interval',
            fill='tonexty',  # Fill to the next trace (upper bound)
            line=dict(width=0),  # No line, just the fill
            fillcolor='rgba(0, 0, 255, 0.2)',  # Transparent blue color
            showlegend=False
        ))

        # Customize the layout
        fig.update_layout(
            title='Forecast vs Training Data',
            xaxis_title='Date',
            yaxis_title='Value',
            template='plotly_white'
        )

        # figure = plot_plotly(model, forecast)
        
        return fig, message
        
        
        logger.warning("Attempted to perform predictions, but this is not implemented yet!")

    def comparison(self, eo_request: EORequest):
        logger.warning("Attempted comparison of two datasets, but this is not implemented yet!")
        
    def _get_dataframe_from_eorequest(self, eo_request: EORequest):
        
        ds_filtered = self._get_filtered_dataset(eo_request)
        
        # Extract year and month from time coordinates for labeling
        #months = ds_filtered['time'].dt.strftime('%Y-%m-%d').values
        #monthly_means = ds_filtered[eo_request.variable_short_name].groupby('time.month').mean(dim=['latitude', 'longitude']).values 
        
        df = pd.DataFrame({
            'ds': ds_filtered["time"].dt.strftime('%Y-%m-%d').values,
            'y': ds_filtered[eo_request.variable_short_name].mean(dim=['latitude', 'longitude']).values
            })       

        return df
    
    
    def _get_filtered_dataset(self, eo_request: EORequest):
        
        ds = eo_request.data.sel(time=slice("2018-01-01", "2020-12-31"))
        
        obbox = eo_request.original_bounding_box
        
        north = obbox['north']
        south = obbox['south']
        east = obbox['east']
        west = obbox['west']

        # Filter the dataset for the original bounding box
        ds_filtered = ds.sel(latitude=slice(south, north), longitude=slice(west, east))
        
        if ds_filtered['latitude'].size == 0 or ds_filtered['longitude'].size == 0:
            logger.warning("Filtered dataset is empty using the exact original bounding box. Trying to include nearest points.")

            # Get the nearest latitude and longitude points
            nearest_lat = ds['latitude'].sel(latitude=[south, north], method='nearest')
            nearest_lon = ds['longitude'].sel(longitude=[west, east], method='nearest')

            # Perform the nearest neighbor selection
            ds_filtered = ds.sel(latitude=nearest_lat, longitude=nearest_lon)
            # Check dimensions of t2m
            logger.debug(f"Nearest point filtered dataset dimensions: {ds_filtered.dims}")
            logger.debug(f"Nearest point filtered dataset latitude range: {ds_filtered['latitude'].min().item()} to {ds_filtered['latitude'].max().item()}")
            logger.debug(f"Nearest point filtered dataset longitude range: {ds_filtered['longitude'].min().item()} to {ds_filtered['longitude'].max().item()}")
        
        return ds_filtered
        
    def get_monthly_mean_dataframe(self, eo_request: EORequest):
        """
        Calculate monthly mean values for a specified variable from the processed dataset.
        
        Parameters:
            ds (xarray.Dataset): The processed dataset.
            variable_name (str): The name of the variable to calculate the mean for.

        Returns:
            months (list): List of months (formatted as 'YYYY-MM').
            monthly_means (list): List of monthly mean values.
        """
        ds_filtered = self._get_filtered_dataset(eo_request)
                        
        # Extract year and month from time coordinates for labeling
        months = ds_filtered['time'].dt.strftime('%Y-%m-%d').values
        monthly_means = ds_filtered[eo_request.variable_short_name].groupby('time.month').mean(dim=['latitude', 'longitude']).values 
        
        df = pd.DataFrame({
            'time': months,
            'value': monthly_means
            })
        
        monthly_means = df.groupby('time').mean()

        max_value = monthly_means['value'].max()
        
        max_month = monthly_means['value'].idxmax()
        
        return df
    


    
    def get_plot_from_dataframe(self, df: pd.DataFrame, yaxis_title):
        figure = px.line(df, x='time', y='value', title="Means over area of interest")
        figure.update_layout(yaxis_title = yaxis_title, xaxis_title = "Time")
        return figure
    
    def get_min_max_from_dataframe(self, df: pd.DataFrame):
        minima = df['value'].min()
        maxima = df['value'].max()
        return Utilities.significant_round(minima, 4), Utilities.significant_round(maxima, 4)
    
    def get_std_from_dataframe(self, df: pd.DataFrame):
        standard_deviation = df['value'].std()
        return Utilities.significant_round(standard_deviation, 4)
        
    
    def get_basic_analysis_string(self, minval: float, maxval: float, std: float, unit: str):
        unformatted_string = Utilities.load_config_file("yaml/analysis.yaml")["basic_analysis"]
        temp_prompt = string.Template(unformatted_string)
        constructed_string = temp_prompt.safe_substitute(
            {'standard_deviation' : std,
             'min_val': minval,
             'max_val': maxval,
             'unit': unit})        
               
        return constructed_string
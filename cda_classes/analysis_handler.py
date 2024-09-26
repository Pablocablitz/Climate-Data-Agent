import xarray as xr
import plotly.express as px
import plotly.graph_objs as go
import string
import pandas as pd
import numpy as np

from utils.utils import Utilities
from .eorequest import EORequest
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components
from dateutil.relativedelta import relativedelta
from loguru import logger
from utils.utils import apply_timing_decorator


@apply_timing_decorator
class AnalysisHandler():
    def __init__(self):
        self.analysis_types = "basic_analysis, predictions, comparison"
        self.colors = [
            '#1f77b4',  # Muted Blue
            '#ff7f0e',  # Soft Orange
            '#2ca02c',  # Calm Green
            '#d62728',  # Warm Red
            '#9467bd',  # Light Purple
            '#8c564b',  # Earthy Brown
            '#e377c2',  # Pink Accent
            '#7f7f7f',  # Neutral Gray
            '#bcbd22',  # Olive Green
            '#17becf'   # Teal
        ]
    
    def basic_analysis(self, eo_request: EORequest):
        # a basic analysis contains:
        # * minima and maxima
        # * standard deviation
        figures = []
        messages = []
        for request in eo_request.collected_sub_requests:
            df = self.get_monthly_mean_dataframe(request)
        
            minval, maxval = self.get_min_max_from_dataframe(df)
            
            figure = self.get_plot_from_dataframe(df, eo_request.variable_long_name + " [" + eo_request.variable_units + "]")
            message = self.get_basic_analysis_string(minval, maxval, self.get_std_from_dataframe(df), eo_request.variable_units)
            figures.append(figure)
            messages.append(message)
            
        return figures, messages

    def significant_event_detection(self, eo_request: EORequest):
        # * Outlier/Anomaly detection
        logger.warning("Attempted significant event detection, but this is not implemented yet!")

    def predictions(self, eo_request: EORequest):
        figures = []
        messages = []
        for request in eo_request.collected_sub_requests:
            df = self._get_dataframe_from_eorequest(request)
            print(df)
            model = Prophet()
            
            model.fit(df)
            
            # figure out what a period is, possibly calculate timesteps in order to ensure predicitons are always for e.g. 1 year
            future = model.make_future_dataframe(periods=request.timeframe_object.prediction_number*365)
            forecast = model.predict(future)
            message = f"The following prediction was performed based on the downloaded data. The prediction encompasses {request.timeframe_object.prediction_number*365} periods [TBC]"
            messages.append(message)
            
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
            figures.append(fig)
        # figure = plot_plotly(model, forecast)
        
        return figures, messages
        
    
    def comparison(self, eo_request: EORequest):
        figures = []
        messages = []
        if eo_request.multi_loc_request == True:
            fig = go.Figure()
            for sub_request, color in zip(eo_request.collected_sub_requests, self.colors):
                df = self._get_dataframe_from_eorequest(sub_request)
                fig = self.get_plotly_figure_multi_loc(fig, df, eo_request.variable_long_name, sub_request.location, color)
                formatted_loc_string = Utilities.join_locations(eo_request.request_locations)
                message = f"Comparing the locations {formatted_loc_string}"
                messages.append(message)
            figures.append(fig)    
            return figures, messages
        
        elif eo_request.multi_time_request == True:
        
            length_intervall = []
            
            # Convert timeframes into total months for comparison
            for timeframe in eo_request.request_timeframes:
                delta = relativedelta(timeframe.enddate, timeframe.startdate)
                total_months = delta.years * 12 + delta.months
                length_intervall.append(total_months)
            
            first_interval = length_intervall[0]  # Reference interval
            
            # Assume intervals are the same until proven otherwise
            eo_request.intervall_same_length = True
            
            for interval in length_intervall[1:]:
                if interval != first_interval:
                    eo_request.intervall_same_length = False
                    break  # Intervals differ
            print(f'intervall same lenght : {eo_request.intervall_same_length}')
            time_ranges = []
            fig = go.Figure()  # Initialize empty figure
            used_colors = []
            
            # Iterate over each request and generate the plot
            for sub_request in eo_request.collected_sub_requests:
                df = self._get_dataframe_from_eorequest(sub_request)
                start_date = sub_request.timeframe_object.startdate_str
                end_date = sub_request.timeframe_object.enddate_str
                time_ranges.append(f"{start_date}-{end_date}")
                
                        # Select a color that hasn't been used yet
                for color in self.colors:
                    if color not in used_colors:
                        # Use the first unused color and add to used_colors
                        used_colors.append(color)
                        break
                else:
                    # If all colors are used, repeat colors by cycling through them
                    color = self.colors[len(used_colors) % len(self.colors)]
                    used_colors.append(color)
                    
                # Update the figure by passing it to get_plotly_figure_multi_time
                fig = self.get_plotly_figure_multi_time(fig, df, eo_request.variable_long_name, color, eo_request.intervall_same_length, sub_request.timeframe_object)
                
            print(used_colors)
            formatted_time_ranges = " and ".join(time_ranges)
            figures.append(fig)  # Store the figure
            messages.append(f"Comparing the time ranges: {formatted_time_ranges}")  # Add the comparison message
        
            return figures, messages
        
    def _get_dataframe_from_eorequest(self, request):
        
        ds_filtered = self._get_filtered_dataset(request)
        
        # Extract year and month from time coordinates for labeling
        #months = ds_filtered['time'].dt.strftime('%Y-%m-%d').values
        #monthly_means = ds_filtered[eo_request.variable_short_name].groupby('time.month').mean(dim=['latitude', 'longitude']).values 
        
        df = pd.DataFrame({
            'ds': ds_filtered["time"].dt.strftime('%Y-%m-%d').values,
            'y': ds_filtered.mean(dim=['latitude', 'longitude']).values
            })       

        return df
    
    
    def _get_filtered_dataset(self, request):
        
        start_date = request.timeframe_object.startdate_str
        end_date = request.timeframe_object.enddate_str
        # Select time range first
        ds = request.data.sel(time=slice(start_date, end_date))
                
        # Loop through each bounding box corresponding to different locations
        obbox = request.obbox
        north = obbox['north']
        south = obbox['south']
        east = obbox['east']
        west = obbox['west']
            
        # Filter the dataset for the current bounding box
        ds_filtered = ds.sel(latitude=slice(south, north), longitude=slice(west, east))
        
        if ds_filtered['latitude'].size == 0 or ds_filtered['longitude'].size == 0:
            logger.warning("Filtered dataset is empty using the exact original bounding box. Trying to include nearest points.")
            
            # Get the nearest latitude and longitude points
            nearest_lat = ds['latitude'].sel(latitude=[south, north], method='nearest')
            nearest_lon = ds['longitude'].sel(longitude=[west, east], method='nearest')
            
            # Perform the nearest neighbor selection
            ds_filtered = ds.sel(latitude=nearest_lat, longitude=nearest_lon)
            
            # Log details about the nearest point selection
            logger.debug(f"Nearest point filtered dataset dimensions: {ds_filtered.dims}")
            logger.debug(f"Nearest point filtered dataset latitude range: {ds_filtered['latitude'].min().item()} to {ds_filtered['latitude'].max().item()}")
            logger.debug(f"Nearest point filtered dataset longitude range: {ds_filtered['longitude'].min().item()} to {ds_filtered['longitude'].max().item()}")
        
        # Append the filtered dataset for this location
        
            
        return ds_filtered
        
    def get_monthly_mean_dataframe(self, request):
        """
        Calculate monthly mean values for a specified variable from the processed dataset.
        
        Parameters:
            ds (xarray.Dataset): The processed dataset.
            variable_name (str): The name of the variable to calculate the mean for.

        Returns:
            months (list): List of months (formatted as 'YYYY-MM').
            monthly_means (list): List of monthly mean values.
        """
        ds_filtered = self._get_filtered_dataset(request)
        print(type(ds_filtered))
        # Extract year and month from time coordinates for labeling
        months = ds_filtered['time'].dt.strftime('%Y-%m-%d').values
        monthly_means = ds_filtered.groupby('time.month').mean(dim=['latitude', 'longitude']).values 
        
        df = pd.DataFrame({
            'time': months,
            'value': monthly_means
            })
        
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
    
    def get_dataframes_from_multi_eorequest(self, eo_request: EORequest):
        filtered_datasets = self._get_filtered_dataset(eo_request)
                
        dataframes = []
        
        for idx, dataset in enumerate(filtered_datasets):
            months = dataset['time'].dt.strftime('%Y-%m-%d').values
            monthly_means = dataset.sel(new_dim=idx).groupby('time.month').mean(dim=['latitude', 'longitude']).values
            
            df = pd.DataFrame({
                f'time_{idx + 1}': months,
                f'value_{idx + 1}': monthly_means
            })
            
            dataframes.append(df)
        
        return dataframes
    
    def get_plotly_figure_multi_loc(self, fig:go.Figure, df, variable_name, location, color):        
       
        fig.add_trace(go.Scatter(
            x=df[f'ds'],
            y=df[f'y'],
            mode='lines',
            name=f'{location}',
            line=dict(color=color)  # Set the color for each trace
        ))

        # Customize layout
        fig.update_layout(
            title='Monthly Means Comparison',
            xaxis_title='Time',
            yaxis_title=variable_name,
            legend_title='Datasets',
            template='plotly'
        )
        
        return fig
    
    def get_plotly_figure_multi_time(self, fig: go.Figure, df, variable_name, color, intervall_same_length, timeframe):
        
        # Handle same-length intervals
        if intervall_same_length:
            
            
            
            # Ensure 'ds' is in datetime format
            df['date'] = pd.to_datetime(df['ds'])
            
            # Extract month and year
            df['month'] = df['date'].dt.month
            df['year'] = df['date'].dt.year
            df['day'] = df['date'].dt.day 
            
            # Determine the number of years in the dataset
            num_years = df['year'].nunique()
            
            # Create a repeated month pattern for x-axis
            df['month_label'] = df['date'].dt.strftime('%b')  # Get month as short name (e.g., Jan, Feb, ...)
            
            # Create a unique x-value for each day in the dataset
            df['x_value'] = (df['year'] - df['year'].min()) * 365 + df['date'].dt.dayofyear  # Unique value for each day across years
            
            
            total_days = (df['year'].max() - df['year'].min() + 1) * 365

            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

            # Initialize tick values and labels
            tickvals = []
            ticktext = []
            month_labels = month_names * num_years
            tickvals = [i * (total_days / (12 * num_years)) + (total_days / (12 * num_years)) / 2 for i in range(12 * num_years)]            
            ticktext = month_labels

            # Reset the x-axis ticks before adding the trace
            fig.update_xaxes(tickvals=[], ticktext=[])  # Clear previous ticks
            
            # Add traces to the figure
            fig.add_trace(go.Scatter(
                x=df['x_value'],  # Unique x values based on year and month
                y=df['y'],        # Variable values
                mode='lines',  # Optional: Add markers for visibility
                name=f'{timeframe.startdate_str}-{timeframe.enddate_str}',  # Label for the trace
                line=dict(color=color)  # Set a unique color for each trace
            ))

            # Customize layout for same-length intervals
            fig.update_layout(
                title='Time Frame Comparison',
                xaxis_title='Months',
                yaxis_title=variable_name,
                legend_title='Datasets',
                template='plotly',
                xaxis=dict(
                    tickvals=tickvals,  # Set ticks for each day of the year
                    ticktext=ticktext,  # Month-Day labels
                    title='Month Day'
                )
            )
        # Handle different-length intervals (normalize by day of the year)
        else:
            df['date'] = pd.to_datetime(df['ds'])  # Ensure 'ds' is in datetime format

            # Extract year, month, and day of year for normalization
            df['year'] = df['date'].dt.year
            df['month'] = df['date'].dt.month
            df['day_of_year'] = df['date'].dt.dayofyear

            # Optionally, combine month and day_of_year as 'Month-Day' for x-axis labels
            df['month_day'] = df['date'].dt.strftime('%b %d')  # E.g., 'Jan-15'

            # Loop through each year and add a trace for each year
            for year, colour in zip(df['year'].unique(), self.colors):
                df_year = df[df['year'] == year]
                
                fig.add_trace(go.Scatter(
                    x=df_year['month_day'],  # Combine Month and Day as the x-axis
                    y=df_year['y'],          # Values
                    mode='lines',
                    name=str(year),          # Name of the trace (year)
                    line=dict(color=colour, width=2),  # Set color and width
                    hovertemplate='Month-Day: %{x}<br>Value: %{y}'  # Tooltip formatting
                ))

            # Customize layout for different-length intervals
            fig.update_layout(
                title="Comparison of Years Over Time by Month and Day",
                xaxis_title="Month-Day",
                yaxis_title=variable_name,
                legend_title="Year",
                hovermode="x unified",  # Unified hover mode
                xaxis=dict(
                    tickmode='array',  
                    tickvals=[15, 45, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349],
                    ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    range=[1, 365]
                )
            )
        
        return fig
    
    def extract_years_from_dates(self, multi_time_ranges, timeframe):
        years = set()
        
        if multi_time_ranges:
            # Iterate over pairs of dates if multi_time_ranges is True
            for i in range(0, len(timeframe), 2):
                start_date = timeframe[i]
                end_date = timeframe[i+1]
                
                # Add each year in the range to the set
                for year in range(start_date.year, end_date.year + 1):
                    years.add(year)
        else:
            # Single time range case
            start_date = timeframe[0]
            end_date = timeframe[1]
            
            # Add each year in the range to the set
            for year in range(start_date.year, end_date.year + 1):
                years.add(year)
        
        # Sort years and convert to list of strings
        years = sorted(str(year) for year in years)
        
        return years
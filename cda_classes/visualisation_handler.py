import plotly.express as px
import xarray as xr

from cda_classes.eorequest import EORequest
from utils.utils import apply_timing_decorator

# Class to visualize the data that the user requested in form of an animation 
@apply_timing_decorator
class VisualisationHandler():
    def __init__(self):
        pass
    
    def visualise_data(self, eorequest: EORequest):
        
        animation = self.generate_plotly_animation(eorequest)
        
        return animation
    
    def generate_plotly_animation(self, eorequest: EORequest): 
        arrays_to_concat = []
            
            # Loop through each location in the request
        for sub_request in eorequest.collected_sub_requests:
            # Append the data array corresponding to the current location
            arrays_to_concat.append(sub_request.data)
        
        # Concatenate all the data arrays along a new dimension 'new_dim'
        dataset = xr.concat(arrays_to_concat, dim='new_dim')   
        df = dataset.to_dataframe(name=eorequest.variable_long_name).reset_index()
        df = df.dropna(subset=[eorequest.variable_long_name])
        
        max_lat = df['latitude'].max()
        min_lat = df['latitude'].min()
        max_lon = df['longitude'].max()
        min_lon = df['longitude'].min()
        
        center_lat = min_lat + (max_lat - min_lat) * 0.5
        center_lon = min_lon + (max_lon - min_lon) * 0.5
        
        # Generating the animation with plotly express module 
        # powered by open street map
        figure = px.density_mapbox(
            
            df, lat=df['latitude'], 
            lon=df['longitude'], 
            z=df[eorequest.variable_long_name],
            radius=8, 
            animation_frame="valid_time", 
            opacity = 0.5, 
            color_continuous_scale =eorequest.variable_cmap,
            width = 640, 
            height = 500, 
            range_color=[int(eorequest.vmin),int(eorequest.vmax)]
            
        )
        
        figure.update_layout(
            mapbox_style="carto-positron", 
            mapbox_zoom=4.5, mapbox_center = {"lat": center_lat, "lon": center_lon}
        )

        figure.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        
        return figure

    def find_coord_name(self, coord_names, pattern):
        """
        Function to find coordinate names using regex

        """
        for name in coord_names:
            if pattern.search(name):
                return name
        return None
    
        
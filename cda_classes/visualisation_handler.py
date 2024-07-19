import numpy as np
from loguru import logger
from matplotlib import pyplot as plt
import re 
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.animation import FuncAnimation
from data_handler.data_handler import DataHandler


import uuid 

import matplotlib.image as mpimg

class VisualisationHandler():
    def __init__(self):
        pass
    def visualise_data(self, data_handler: DataHandler):
        self.cds_data = data_handler.request_cds
        self.generate_climate_animation()
        
    def generate_climate_animation(self):
        """
        Generate an animation of temperature data.
        """
        
        # lat_pattern = re.compile(r'lat(itude)?', re.IGNORECASE)
        # lon_pattern = re.compile(r'lon(gitude)?', re.IGNORECASE)
        # coord_names = self.cds_data.ds.coords.keys()
        lat_name = 'latitude'
        lon_name = 'longitude'
        

        
        # Define the wider area bounds (adjust these as needed)
        lon_min, lon_max = self.cds_data.ds[lon_name].min().values, self.cds_data.ds[lon_name].max().values
        lat_min, lat_max = self.cds_data.ds[lat_name].min().values, self.cds_data.ds[lat_name].max().values
            
        # Calculate vmin and vmax for colorbar
        vmin = self.cds_data.ds[self.cds_data.variable_short_name].min()  # minimum temperature value
        vmax = self.cds_data.ds[self.cds_data.variable_short_name].max() # maximum temperature value
        
        fig = plt.figure(figsize=(12, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())  # Adjust the extent

        ax.add_feature(cfeature.LAND, edgecolor='black', facecolor='lightgray')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        print(self.cds_data.ds)
        
        # Extract DataArray from Dataset for the specified time index
        data_array = self.cds_data.ds[self.cds_data.variable_short_name].isel(time=0)  # Extracting DataArray for the first time step
        
        # Extract longitude and latitude arrays
        lon = self.cds_data.ds[lon_name]
        lat = self.cds_data.ds[lat_name]
        

        heatmap = ax.pcolormesh(lon, lat, data_array,
                                cmap=self.cds_data.variable_cmap, vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())
        cbar = plt.colorbar(heatmap, ax=ax, orientation='horizontal', pad=0.05, extend='both')
        cbar.set_label(f'{self.cds_data.product} [{self.cds_data.variable_units}]')
        ax.set_title(f'{self.cds_data.product} Animation', fontsize=16)
        
        try:
            # Load the location marker icon image (replace with your own image path)
            icon_img = mpimg.imread('/home/eouser/miniconda3/envs/spacy_env/ERA_DATA/config_data/map.png')  # Adjust the path as needed
            
            # Example location coordinates (replace with your desired coordinates)
            location_lon = lon_min + (lon_max - lon_min) * 0.5
            location_lat = lat_min + (lat_max - lat_min) * 0.5

            # Place the icon image on the map
            ax.imshow(icon_img, extent=[location_lon - 0.3, location_lon + 0.3, location_lat - 0.3, location_lat + 0.3],
                    transform=ccrs.PlateCarree(), zorder=10)
        except Exception as e:
            logger.error(f"Error getting icon: {e}")
            return {}

        # Initialize the plot elements
        mesh = ax.pcolormesh(lon, lat, data_array,
                            cmap=self.cds_data.variable_cmap, transform=ccrs.PlateCarree())
        # Function to update the plot for each frame of the animation
        def update(frame):
            # Update the data for the pcolormesh
            new_data = self.cds_data.ds[self.cds_data.variable_short_name].isel(time=frame).values
            mesh.set_array(new_data.flatten())
            
            # Update the title with the current date
            date_str = np.datetime_as_string(self.cds_data.ds.time[frame].values, unit="D")
            ax.set_title(f'{self.cds_data.product} on {date_str} in {self.cds_data.location}', fontsize=16)

            return [mesh] 

        # Create the animation
        animation = FuncAnimation(fig, update, frames=len(self.cds_data.ds.time), interval=200, blit=True)
        animation_uuid = uuid.uuid4()
        self.output_path = f'results/animation_{animation_uuid}.mp4'    # Display the animation
        animation.save(self.output_path, writer='ffmpeg', fps=4 )
        plt.close()  # Close initial plot to prevent duplicate display
        

    
    def find_coord_name(self, coord_names, pattern):
        """
        Function to find coordinate names using regex

        """
        for name in coord_names:
            if pattern.search(name):
                return name
        return None
    
        
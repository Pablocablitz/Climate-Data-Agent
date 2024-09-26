import plotly.express as px
import xarray as xr

from cda_classes.eorequest import EORequest

class VisualisationHandler():
    def __init__(self):
        pass
    def visualise_data(self, eorequest: EORequest):
        
        animation = self.generate_plotly_animation(eorequest)
        
        return animation
    # def generate_climate_animation(self, eorequest):
    #     """
    #     Generate an animation of temperature data.
    # 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
    #     """
        
    #     lat_name = 'latitude'
    #     lon_name = 'longitude'
        
    #     # Define the wider area bounds (adjust these as needed)
    #     lon_min, lon_max = eorequest.data[lon_name].min().values, eorequest.data[lon_name].max().values
    #     lat_min, lat_max = eorequest.data[lat_name].min().values, eorequest.data[lat_name].max().values
            
    #     # Calculate vmin and vmax for colorbar
    #     vmin = eorequest.vmin  # minimum temperature value
    #     vmax = eorequest.vmax # maximum temperature value
        
    #     fig = plt.figure(figsize=(8, 8))
    #     ax = plt.axes(projection=ccrs.PlateCarree())
    #     ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=ccrs.PlateCarree())  # Adjust the extent

    #     ax.add_feature(cfeature.LAND, edgecolor='black', facecolor='lightgray')
    #     ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    #     ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        
    #     # Extract DataArray from Dataset for the specified time index
    #     data_array = eorequest.data[eorequest.variable_short_name].isel(time=0)  # Extracting DataArray for the first time step
        
    #     # Extract longitude and latitude arrays
    #     lon = eorequest.data[lon_name]
    #     lat = eorequest.data[lat_name]
        

    #     heatmap = ax.pcolormesh(lon, lat, data_array,
    #                             cmap=eorequest.variable_cmap, vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())
    #     cbar = plt.colorbar(heatmap, ax=ax, orientation='vertical', pad=0.02, aspect=40, fraction=0.05, extend='both')
    #     cbar.set_label(f'{eorequest.request_product[0]} {eorequest.variable_units}')
    #     ax.set_title(f'{eorequest.request_product[0]} Animation', fontsize=16)
        
    #     try:
    #         img_png = cairosvg.svg2png(url="./assets/pin.svg", scale=2.0)
    #         icon_img = Image.open(BytesIO(img_png))
            
    #         # Example location coordinates (replace with your desired coordinates)
    #         location_lon = lon_min + (lon_max - lon_min) * 0.5
    #         location_lat = lat_min + (lat_max - lat_min) * 0.5

    #         # Place the icon image on the map
    #         ax.imshow(icon_img, extent=[location_lon - 0.3, location_lon + 0.3, location_lat - 0.3, location_lat + 0.3],
    #                 transform=ccrs.PlateCarree(), zorder=10)
    #     except Exception as e:
    #         logger.error(f"Error getting icon: {e}")
    #         return {}

    #     # Initialize the plot elements
    #     mesh = ax.pcolormesh(lon, lat, data_array,
    #                         cmap=eorequest.variable_cmap, vmin=vmin, vmax=vmax, transform=ccrs.PlateCarree())
    #     # Function to update the plot for each frame of the animation
    #     def update(frame):
    #         # Update the data for the pcolormesh
    #         new_data = eorequest.data[eorequest.variable_short_name].isel(time=frame).values
    #         mesh.set_array(new_data.flatten())
            
    #         # Update the title with the current date
    #         date_str = np.datetime_as_string(eorequest.data.time[frame].values, unit="D")
    #         ax.set_title(f'{eorequest.request_product[0]} on {date_str} in {eorequest.request_location[0]}', fontsize=16)

    #         return [mesh] 

    #     # Create the animation
    #     animation = FuncAnimation(fig, update, frames=len(eorequest.data.time), interval=200, blit=True)
    #     animation_uuid = uuid.uuid4()
    #     self.output_path = f'results/animation_{animation_uuid}.mp4'    # Display the animation
    #     animation.save(self.output_path, writer='ffmpeg', fps=10 )
    #     plt.close()  # Close initial plot to prevent duplicate display
        
    
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
        
        
        figure = px.density_mapbox(df, lat=df['latitude'], lon=df['longitude'], z=df[eorequest.variable_long_name],
                                        radius=8, animation_frame="valid_time", opacity = 0.5, color_continuous_scale =eorequest.variable_cmap,
                                        width = 640, height = 500, range_color=[int(eorequest.vmin),int(eorequest.vmax)])
        figure.update_layout(mapbox_style="carto-positron", mapbox_zoom=4.5, mapbox_center = {"lat": center_lat, "lon": center_lon})

        figure.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        # figure.update_layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 30
        # figure.update_layout(updatemenus = [dict(buttons = [dict(
        #                                        args = [None, {"frame": {"duration": 50, 
        #                                                                 "redraw": False},
        #                                                       "fromcurrent": True, 
        #                                                       "transition": {"duration": 20}}])])])
        
        return figure
    
    def generate_plot(self):
        pass
        

    
    def find_coord_name(self, coord_names, pattern):
        """
        Function to find coordinate names using regex

        """
        for name in coord_names:
            if pattern.search(name):
                return name
        return None
    
        
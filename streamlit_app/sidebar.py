import streamlit as st
from datetime import datetime, timedelta
        
        
        
        
        


# Get today's date


def sidebar():
    today = datetime.now()

    # Calculate the date 7 days ago
    seven_days_ago = today - timedelta(days=7)

    time_period_list = ["From", "01-01-1950", "To", seven_days_ago.strftime('%d-%m-%Y')]

    st.markdown("<hr style='border: 1px solid #FFCC4D;'>", unsafe_allow_html=True)
    st.subheader("Available Variables - ERA-5-Land")
    variable_list = ["2m Temperature", "Skin Temperature", "Total Precipitation", "10m Wind Speed", "Snow Depth", "Evapuration"]
    variable_explanations = {
        "2m Temperature": "Temperature of air at 2m above the surface of land, sea or in-land waters. 2m temperature is calculated by interpolating between the lowest model level and the Earth's surface, taking account of the atmospheric conditions. ",
        "Skin Temperature": "Temperature of the surface of the Earth. The skin temperature is the theoretical temperature that is required to satisfy the surface energy balance. It represents the temperature of the uppermost surface layer, which has no heat capacity and so can respond instantaneously to changes in surface fluxes. Skin temperature is calculated differently over land and sea.",
        "Total Precipitation": "Accumulated liquid and frozen water, including rain and snow, that falls to the Earth's surface. It is the sum of large-scale precipitation (that precipitation which is generated by large-scale weather patterns, such as troughs and cold fronts) and convective precipitation (generated by convection which occurs when air at lower levels in the atmosphere is warmer and less dense than the air above, so it rises). Precipitation variables do not include fog, dew or the precipitation that evaporates in the atmosphere before it lands at the surface of the Earth.",  
        "10m Wind Speed": "This parameter is the horizontal speed of the wind, or movement of air, at a height of ten metres above the surface of the Earth.",
        "Snow Depth": "Instantaneous grib-box average of the snow thickness on the ground (excluding snow on canopy).",
        "Evapuration": "Accumulated amount of water that has evaporated from the Earth's surface, including a simplified representation of transpiration (from vegetation), into vapour in the air above."  
        }    
    row1 = st.columns(3)
    row2 = st.columns(3)
    for idx, col in enumerate(row1 + row2):
        if idx < len(variable_list):
            variable = variable_list[idx]
            with col:
                with st.popover(variable, use_container_width=30):
                    st.write(variable_explanations.get(variable, "No explanation available."))

    st.markdown("<hr style='border: 1px solid #FFCC4D;'>", unsafe_allow_html=True)
    st.subheader("Available Locations")
    with st.container(border = True):
        st.write("Every Location is possible! Please try to use the correct name.")
    st.markdown("<hr style='border: 1px solid #FFCC4D;'>", unsafe_allow_html=True)
    st.subheader("Available Time")
    
    row3 = st.columns(4)
    for idx, col in enumerate(row3):
        if idx < len(time_period_list):
            with col:
                tile = col.container(height=50)
                tile.write(time_period_list[idx])
    
    analysis_type_list = ["Basic Analysis", "Comparison", "Prediction"]
    analysis_type_explanations = {
        "Basic Analysis": (
            "Basic Analysis provides fundamental statistical insights into the dataset and is the default mode when no Analysis Type was selected. "
            "It includes the calculation of the minimum and maximum values, as well as the standard deviation. "
            "This analysis is useful for understanding the overall range and variability of the data."
        ),
        "Comparison": (
            "Comparison analysis allows for the evaluation of differences between multiple data points. "
            "It can compare data across different locations or between different time periods. "
            "For multi-location comparisons, it visualizes data from multiple locations side-by-side. "
            "For multi-time comparisons, it contrasts data from two distinct time ranges to identify temporal changes."
        ),
        "Prediction": (
            "Prediction analysis uses historical data to forecast future trends. "
            "By applying predictive modeling techniques, such as time series forecasting with Prophet, "
            "this analysis generates predictions for a specified future period. "
            "The output includes forecasted data points along with a confidence interval for each prediction."
        ),
    }
    st.markdown("<hr style='border: 1px solid #FFCC4D;'>", unsafe_allow_html=True)
    st.subheader("Available Analysis Types")
    row4 = st.columns(3)
    for idx, col in enumerate(row4):
        if idx < len(analysis_type_list):
            with col:
                analysis_type = analysis_type_list[idx]
                with st.popover(analysis_type, use_container_width=30):
                    st.write(analysis_type_explanations.get(analysis_type, "No explanation available."))
                    
                    
                    

    st.markdown("<hr style='border: 1px solid #FFCC4D;'>", unsafe_allow_html=True)
    
    st.header("Examples")
    container_data = [
        "Show me the Temperature of Rome between 2015 and 2020",
        "Compare the Precipitation of Rome and London between 2015 and 2020",
        "Show me a Prediction of the Temperature of London between 2020 to 2023"
    ]
    for idx, prompt in enumerate(container_data):
        with st.popover(f"{prompt}", use_container_width=100):
            st.write(f"{prompt}")
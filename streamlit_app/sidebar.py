import streamlit as st

from datetime import datetime, timedelta
        
def sidebar():
    # Load the local image
    logo_path = (
        "/my_volume/programming/Climate-Data-Agent/assets/"
        "ESA_logo_Tagline_WT_EN.png"
    )

    # Use columns to display text and image side by side in the sidebar
    col1, col2 = st.columns([1, 1], vertical_alignment="center")

    # Title in the first column
    col1.title("Documentation")

    # Image in the second column
    col2.image(logo_path, width=200)
    today = datetime.now()

    # Calculate the date 7 days ago
    seven_days_ago = today - timedelta(days=7)

    time_period_list = [
        "From", "01-01-1950", "To", seven_days_ago.strftime('%d-%m-%Y')
    ]

    st.markdown(
        "<hr style='border: 1px solid #FFCC4D;'>", unsafe_allow_html=True
    )
    st.subheader("Available Variables - ERA-5-Land")

    variable_list = [
        "2m Temperature", "Skin Temperature", "Total Precipitation",
        "10m Wind Speed", "Snow Depth", "Evapuration"
    ]

    variable_explanations = {
        "2m Temperature": (
            "Temperature of air at 2m above the surface of land, sea or in-land "
            "waters. 2m temperature is calculated by interpolating between the "
            "lowest model level and the Earth's surface, taking account of the "
            "atmospheric conditions."
        ),
        "Skin Temperature": (
            "Temperature of the surface of the Earth. The skin temperature is "
            "the theoretical temperature that is required to satisfy the surface "
            "energy balance. It represents the temperature of the uppermost surface "
            "layer, which has no heat capacity and so can respond instantaneously "
            "to changes in surface fluxes. Skin temperature is calculated differently "
            "over land and sea."
        ),
        "Total Precipitation": (
            "Accumulated liquid and frozen water, including rain and snow, that "
            "falls to the Earth's surface. It is the sum of large-scale precipitation "
            "and convective precipitation. Precipitation variables do not include "
            "fog, dew or the precipitation that evaporates in the atmosphere."
        ),
        "10m Wind Speed": (
            "This parameter is the horizontal speed of the wind, or movement of air, "
            "at a height of ten metres above the surface of the Earth."
        ),
        "Snow Depth": (
            "Instantaneous grib-box average of the snow thickness on the ground "
            "(excluding snow on canopy)."
        ),
        "Evapuration": (
            "Accumulated amount of water that has evaporated from the Earth's surface, "
            "including a simplified representation of transpiration (from vegetation)."
        )
    }

    row1 = st.columns(3)
    row2 = st.columns(3)
    for idx, col in enumerate(row1 + row2):
        if idx < len(variable_list):
            variable = variable_list[idx]
            with col:
                with st.popover(variable, use_container_width=30):
                    st.write(variable_explanations.get(variable, "No explanation available."))

    st.markdown(
        "<hr style='border: 1px solid #FFCC4D;'>", unsafe_allow_html=True
    )
    st.subheader("Available Locations")
    with st.container(border=True):
        st.write("Every Location is possible! Please try to use the correct name.")

    st.markdown(
        "<hr style='border: 1px solid #FFCC4D;'>", unsafe_allow_html=True
    )
    st.subheader("Available Time")

    row3 = st.columns(4)
    for idx, col in enumerate(row3):
        if idx < len(time_period_list):
            with col:
                tile = col.container(height=50)
                tile.write(time_period_list[idx])

    analysis_type_list = [
        "Basic Analysis", "Comparison", "Prediction"
    ]

    analysis_type_explanations = {
        "Basic Analysis": (
            "**Basic Analysis** provides fundamental statistical insights into "
            "the dataset and serves as the default mode when no specific analysis "
            "type is selected. This analysis includes:\n\n"
            "- **Minimum Value**: The lowest recorded value in the dataset.\n"
            "- **Maximum Value**: The highest recorded value in the dataset.\n"
            "- **Standard Deviation**: A measure of the amount of variation or "
            "dispersion of a set of values.\n\n"
            "This analysis is essential for understanding the overall range and "
            "variability of the data, helping users identify the spread and central "
            "tendency of the dataset."
        ),
        "Comparison": (
            "**Comparison Analysis** enables users to evaluate differences between "
            "multiple data points effectively. It can compare data across:\n\n"
            "- **Different Locations**: Visualizes data from multiple locations "
            "side-by-side, allowing for easy geographical comparisons.\n"
            "- **Different Time Periods**: Contrasts data from two distinct time "
            "ranges to identify temporal changes and trends over time.\n\n"
            "This analysis type is particularly useful for detecting variations in "
            "patterns or behaviors in data collected under different conditions or "
            "timeframes."
        ),
        "Prediction": (
            "**Prediction Analysis** utilizes historical data to forecast future "
            "trends. It applies advanced predictive modeling techniques, such as time "
            "series forecasting with Prophet, to generate predictions for specified "
            "future periods. The output includes:\n\n"
            "- **Forecasted Data Points**: Estimated future values based on historical "
            "trends.\n"
            "- **Confidence Intervals**: Ranges that provide a measure of uncertainty "
            "around each prediction, indicating the reliability of the forecasts.\n\n"
            "This analysis is invaluable for planning and decision-making, as it helps "
            "users anticipate future conditions based on past data."
        )
    }

    st.markdown(
        "<hr style='border: 1px solid #FFCC4D;'>", unsafe_allow_html=True
    )
    st.subheader("Available Analysis Types")

    row4 = st.columns(3)
    for idx, col in enumerate(row4):
        if idx < len(analysis_type_list):
            with col:
                analysis_type = analysis_type_list[idx]
                with st.popover(analysis_type, use_container_width=30):
                    st.write(
                        analysis_type_explanations.get(
                            analysis_type, "No explanation available."
                        )
                    )

    st.markdown(
        "<hr style='border: 1px solid #FFCC4D;'>", unsafe_allow_html=True
    )

    st.header("Examples")

    container_data = [
        "Show me the Temperature of Rome between 2015 and 2020",
        "Compare the Precipitation of Rome and London between 2015 and 2020",
        "Show me a Prediction of the Temperature of London between 2020 to 2023"
    ]

    container_data_pop_up = [
        (
            "### Climate Variable: \n- **Temperature**  \n"
            "### Specified Climate Variable: \n- **2m Temperature**  \n"
            "### Location: \n- **Rome**  \n"
            "### Time Range: \n- **2015-01-01 to 2020-12-31**  \n"
            "### Analysis Type: \n- **Basic Analysis**  \n"
        ),
        (
            "### Climate Variable: \n- **Precipitation**  \n"
            "### Specified Climate Variable: \n- **Total Precipitation**  \n"
            "### Locations: \n- **Rome**  \n- **London**  \n"
            "### Time Range: \n- **2015-01-01 to 2020-12-31**  \n"
            "### Analysis Type: \n- **Comparison**  \n"
        ),
        (
            "### Climate Variable: \n- **Evapuration**  \n"
            "### Specified Climate Variable: \n- **Total Evapuration**  \n"
            "### Location: \n- **London**  \n"
            "### Time Range: \n- **2020-01-01 to 2023-12-31**  \n"
            "### Analysis Type: \n- **Prediction**  \n"
        )
    ]

    for prompt, result in zip(container_data, container_data_pop_up):
        with st.popover(f"{prompt}", use_container_width=100):
            st.write(f"{result}")
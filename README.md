# Climate-Data-Agent
## Setup

### Authentication
In order to download data from the various sources, the user must obtain an API key and properly configure their system for access.

#### CDS
The full process is described [here](https://cds.climate.copernicus.eu/api-how-to#install-the-cds-api-key), but for convenience the basic steps are described here:
1. Register on the CDS platform in order to obtain a UID and an API key
2. Find the UID and API key on the [user profile](https://cds.climate.copernicus.eu/user/317337)
3. Create a .cdsapirc file in the workspace with the format (UID and API key below are just an example):
```
url: https://cds.climate.copernicus.eu/api/v2
key: 123456:1c1c1c1c-1c1c-c1c1-1c11-c04240eb531c
```

## Introduction to this repository
1. Utils contains all necessary functions outside of the classes CDS and LLM
2. Main function is inside of streamlit_app_main
3. Config file includes all the necessary static data for the LLM and the API request of CDS
4. Variable file contains all the necessary information for the climate products

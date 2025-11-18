import ee
import pandas as pd
import geopandas as gpd
from meteostat import Point, Daily
from datetime import datetime
import geemap

# ==============================================================================
# Step 1: Initialize GEE
# ==============================================================================
try:
    # Attempt to initialize Earth Engine
    ee.Initialize()
    print("--- Step 1: Google Earth Engine has been successfully initialized ---")
except Exception as e:
    # If initialization fails, prompt for authentication
    print("Google Earth Engine authorization is required. Running authentication flow...")
    try:
        ee.Authenticate()
        ee.Initialize()
        print("--- Step 1: Google Earth Engine has been successfully initialized after authentication ---")
    except Exception as auth_e:
        print(f"GEE failed to initialize even after authentication. Please ensure you have completed the authorization steps. Error: {auth_e}")
        exit()

# ==============================================================================
# Step 2: Fetch Weather Station Data (Temperature, Wind Speed, Humidity)
# ==============================================================================
print("\n--- Step 2: Fetching summer 2022 weather station data ---")

# Approximate coordinates for Washington, D.C.
dc_lat, dc_lon = 38.9072, -77.0369
start_date = datetime(2022, 6, 1)  # Summer start (June 1st)
end_date = datetime(2022, 8, 31)    # Summer end (August 31st)

# Get daily data from Washington Reagan National Airport (DCA) weather station
station = Point(dc_lat, dc_lon)
data = Daily(station, start_date, end_date)
weather_df = data.fetch()

# Calculate average values for the period
avg_temp_c = weather_df['tavg'].mean()
avg_wind_ms = weather_df['wspd'].mean() * 1000 / 3600  # Convert from km/h to m/s
avg_humidity = weather_df['rhum'].mean()

print(f"Average temperature in summer 2022: {avg_temp_c:.2f} °C")
print(f"Average wind speed in summer 2022: {avg_wind_ms:.2f} m/s")
print(f"Average relative humidity in summer 2022: {avg_humidity:.2f} %")

# ==============================================================================
# Step 3: Obtain Land Surface Temperature (LST) from GEE
# ==============================================================================
print("\n--- Step 3: Obtaining Land Surface Temperature (LST) for each census tract from Google Earth Engine ---")
print("(This may take a few minutes as it is processing a large amount of satellite imagery in the cloud...)")

# a) Load census tract geographical boundaries
try:
    tracts_gdf = gpd.read_file('tl_2022_11_tract.shp')
    # Convert GeoDataFrame to a FeatureCollection that GEE can use
    tracts_ee = geemap.geopandas_to_ee(tracts_gdf)
except Exception as e:
    print(f"Error: Could not load the Shapefile 'tl_2022_11_tract.shp'. Error: {e}")
    exit()

# b) Define a function to mask clouds in Landsat imagery
def cloud_mask_landsat(image):
    # Use the QA band to identify and mask clouds
    qa = image.select('QA_PIXEL')
    cloud_mask = qa.bitwiseAnd(1 << 3).Or(qa.bitwiseAnd(1 << 4))
    return image.updateMask(cloud_mask.Not())

# c) GEE image processing workflow
# Use Landsat 9 Collection 2, Tier 1 Land Surface Temperature product
lst_collection = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
    .filterDate('2022-06-01', '2022-08-31') \
    .filterBounds(tracts_ee.geometry()) \
    .map(cloud_mask_landsat)

# Select the thermal band (ST_B10), apply the scaling factor, and convert to Celsius
def process_lst(image):
    lst = image.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15)
    return lst.copyProperties(image, ['system:time_start'])

lst_processed = lst_collection.map(process_lst)

# Calculate the average land surface temperature for the summer
mean_lst_image = lst_processed.mean()

# d) Calculate the average LST for each census tract
lst_per_tract = mean_lst_image.reduceRegions(
    collection=tracts_ee,
    reducer=ee.Reducer.mean(),
    scale=30  # Resolution of Landsat's thermal band
).select(['GEOID', 'mean'], ['GEOID', 'LST_C'])

# e) Convert the GEE results back to a GeoDataFrame
try:
    lst_gdf = geemap.ee_to_geopandas(lst_per_tract)
    print("Land Surface Temperature data processed and downloaded successfully.")
except Exception as e:
    print(f"Failed to convert data from GEE. This could be due to a network issue or a GEE processing timeout. Error: {e}")
    exit()

# ==============================================================================
# Step 4: Consolidate Data and Export to CSV
# ==============================================================================
print("\n--- Step 4: Consolidating all data and exporting to a CSV file ---")

lst_final_df = lst_gdf[['GEOID', 'LST_C']].copy()

# Add the previously calculated weather station data as new columns
lst_final_df['Avg_Temp_C'] = avg_temp_c
lst_final_df['Avg_Wind_ms'] = avg_wind_ms
lst_final_df['Avg_Humidity_percent'] = avg_humidity

# Merge with census tract names and other information for context
tract_info_df = tracts_gdf[['GEOID', 'NAMELSAD']].rename(columns={'NAMELSAD': 'Tract_Name'})
final_df = pd.merge(tract_info_df, lst_final_df, on='GEOID', how='left')

output_filename = 'dc_tract_thermal_climate_2022.csv'
final_df.to_csv(output_filename, index=False)

print(f"\nSuccess! All thermal climate data has been organized by census tract and saved to: '{output_filename}'")
print("\nFinal data preview:")
print(final_df.head())
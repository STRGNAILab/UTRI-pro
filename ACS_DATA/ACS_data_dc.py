import requests
import pandas as pd

# ==============================================================================
# Step 1: Configure your request
# ==============================================================================

API_KEY = '' # <-- Replace with your API key

# Data variables: NAME denotes geographical names, B19013_001E denotes median household income
# You may add further variables, separated by commas, e.g. 'B01003_001E' (total population)
VARIABLES = 'NAME,B19013_001E'

# Years (ACS5 data)
YEARS = [2023, 2022, 2021, 2020, 2019, 2018]

# Geocode: Washington, D.C.
STATE_FIPS = '11'
COUNTY_FIPS = '001'

# ==============================================================================
# Step 2: Iterate to obtain data
# ==============================================================================
all_data = []

print("Starting to fetch data from the Census API...")

for year in YEARS:
    print(f"  Fetching data for the year {year}...")
    
    # Construct the API request URL
    api_url = (
        f'https://api.census.gov/data/{year}/acs/acs5'
        f'?get={VARIABLES}'
        f'&for=tract:*'
        f'&in=state:{STATE_FIPS}%20county:{COUNTY_FIPS}'
        f'&key={API_KEY}'
    )
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()

        data = response.json()
        
        # The first row contains column names
        df = pd.DataFrame(data[1:], columns=data[0]) 
        
        df['Year'] = year
        
        all_data.append(df)
        
    except requests.exceptions.RequestException as e:
        print(f"    Error: Failed to fetch data for {year}. Error message: {e}")
    except ValueError as e:
        print(f"    Error: Failed to parse data for {year} (likely an invalid JSON response). Error message: {e}")

# ==============================================================================
# Step 3: Clean and consolidate data
# ==============================================================================
if all_data:
    print("\nData fetching complete, now cleaning and consolidating...")
    
    final_df = pd.concat(all_data, ignore_index=True)
    
    final_df = final_df.rename(columns={
        'B19013_001E': 'Median_Household_Income',
        'NAME': 'Tract_Name',
        'state': 'State_FIPS',
        'county': 'County_FIPS',
        'tract': 'Tract_FIPS'
    })
    
    # Create a full GEOID, which is useful for merging with other geospatial data
    final_df['GEOID'] = final_df['State_FIPS'] + final_df['County_FIPS'] + final_df['Tract_FIPS']
    
    final_df['Median_Household_Income'] = pd.to_numeric(
        final_df['Median_Household_Income'], 
        errors='coerce' # 'coerce' will turn non-convertible values into NaN
    )
    
    final_df = final_df[[
        'GEOID', 'Tract_Name', 'Year', 'Median_Household_Income', 
        'State_FIPS', 'County_FIPS', 'Tract_FIPS'
    ]]

    # ==============================================================================
    # Step 4: Save and display the results
    # ==============================================================================
    
    output_filename = 'dc_tract_median_income_2018-2022.csv'
    final_df.to_csv(output_filename, index=False)
    
    print(f"\nSuccess! Data has been saved to the file: {output_filename}")
    
    # Display the first few rows of data
    print("\nData Preview:")
    print(final_df.head())
    
    # Display data summary
    print("\nData Information:")
    final_df.info()

else:
    print("\nFailed to fetch any data. Please check your API key and network connection.")
import pandas as pd
import numpy as np

# Assuming the CSV file from the previous step is named this way
df = pd.read_csv('dc_tract_median_income_2018-2023.csv') 

# --- Statistics of Median Household Income by Year ---
income_stats_by_year = df.groupby('Year')['Median_Household_Income'].describe()

print("--- Statistics of Median Household Income by Year ---")
print(income_stats_by_year)


# --- Overall Income Trend Analysis ---
# Calculate the overall median income for each year (the median of incomes across all census tracts)
overall_median_income = df.groupby('Year')['Median_Household_Income'].median()

print("\n--- Trend of Overall Median Household Income in Washington, D.C. Over the Years ---")
print(overall_median_income)


# --- In-depth Analysis of 2022 Data ---

df_2022 = df[df['Year'] == 2022].copy()

# Find the 5 census tracts with the highest income in 2022
highest_income_2022 = df_2022.nlargest(5, 'Median_Household_Income')

# Find the 5 census tracts with the lowest income in 2022
lowest_income_2022 = df_2022.nsmallest(5, 'Median_Household_Income')

print("\n--- Top 5 Census Tracts by Median Household Income in 2022 ---")
print(tabulate(highest_income_2022[['Tract_Name', 'Median_Household_Income']], headers='keys', tablefmt='pipe', showindex=False))


print("\n--- Bottom 5 Census Tracts by Median Household Income in 2022 ---")
print(tabulate(lowest_income_2022[['Tract_Name', 'Median_Household_Income']], headers='keys', tablefmt='pipe', showindex=False))
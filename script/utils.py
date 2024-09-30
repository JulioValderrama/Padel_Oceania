# utils.py

import pandas as pd

# Cleaning column DATE and converting it to format DateTime
def convert_date(df):
    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
    return df

# Function to format values with max two decimals
def format_value(value):
    return f'{float(value):,.2f}'  # Ensure we restrict to 2 decimal places

# Function to generate period labels dynamically for PDF and Tables printed
def generate_period_label(year, quarter=None, month=None):
    if month:
        # Convert month number to month name
        month_name = pd.to_datetime(f'{year}-{month}-01').strftime('%B')
        return f'{month_name} {year}'
    elif quarter:
        return f'Q{quarter} {year}'
    else:
        return str(year)
    
# Function that will filter Data Frames according to the Period of time, Year, Quarter or Month that the User provides
def filtering_by_year_quarter_month(df, year, quarter=None, month=None):

    # Filter data by year, quarter, or month
    df_filtered = df[df['date'].dt.year == year]

    if quarter is not None:
        df_filtered = df_filtered[df_filtered['date'].dt.quarter == quarter]
    
    if month is not None:
        df_filtered = df_filtered[df_filtered['date'].dt.month == month]

    return df_filtered
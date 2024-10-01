# utils.py

import pandas as pd

# Cleaning column DATE and converting it to format DateTime
def convert_date(df):
    # Convert the 'date' column from 'dd/mm/yyyy' format to datetime
    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', dayfirst=True, errors='coerce')
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

def filter_transactions_before_period(df, year, quarter=None):

    # Ensure the 'date' column is in datetime format
    df['date'] = pd.to_datetime(df['date'])

    # Determine the start date of the next quarter or next year
    if quarter == 1:
        start_date = f'{year}-04-01'  # Q2 starts on April 1st
    elif quarter == 2:
        start_date = f'{year}-07-01'  # Q3 starts on July 1st
    elif quarter == 3:
        start_date = f'{year}-10-01'  # Q4 starts on October 1st
    elif quarter == 4:
        start_date = f'{year + 1}-01-01'  # Q1 of the next year starts on January 1st
    else:
        # If no quarter is provided, include everything before the next year (which covers the whole year)
        start_date = f'{year + 1}-01-01'

    # Convert start_date to datetime for comparison
    start_date = pd.to_datetime(start_date)

    # Filter the DataFrame for transactions before the start of the next quarter or next year
    df_filtered = df[df['date'] < start_date]

    return df_filtered

def get_prior_year_and_quarter(current_year, current_quarter=None):
    # If quarter is provided
    if current_quarter is not None:
        # If the current quarter is 1, the prior quarter is 4, and prior year is current year - 1
        if current_quarter == 1:
            prior_year = current_year - 1
            prior_quarter = 4
        else:
            prior_year = current_year
            prior_quarter = current_quarter - 1
    else:
        # If quarter is None, only return the prior year (subtract 1 from current year)
        prior_year = current_year - 1
        prior_quarter = None
    
    return prior_year, prior_quarter


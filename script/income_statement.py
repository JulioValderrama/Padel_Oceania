# income_statement.py

import pandas as pd
from data import df_inventory, df_expenses, df_income, operational_expenses, other_income
from inventory import update_inventory
from utils import generate_period_label

# Function to update the payment_status from PENDING to COMPLETED for those sales credited and PAID from Amazon in Amazon.csv to Income.csv
def updating_payment_status(income_df, order_id):

    for index, row in income_df.iterrows():

        # Looking for rows with PENDING status and changing it to COMPLETED
        if (row['order_id'] == order_id) and (row['payment_status'] == 'pending'):
            income_df.at[index, 'payment_status'] = 'completed'
    
    
    return income_df

# Function to calculate the COGS
def calculate_cogs(sku, quantity_sold):
    cogs = 0
    remaining_quantity = quantity_sold
    
    # Filter inventory by SKU and sort by batch (FIFO)
    df_inventory_filtered = df_inventory[df_inventory['sku'] == sku].sort_values(by='batch')
    
    for _, row in df_inventory_filtered.iterrows():
        if remaining_quantity == 0:
            break
        available_quantity = row['quantity']
        
        if available_quantity <= remaining_quantity:
            cogs += available_quantity * row['total_cogs']
            remaining_quantity -= available_quantity
        else:
            cogs += remaining_quantity * row['total_cogs']
            remaining_quantity = 0

    return cogs

# Function that will calculate Operational Expenses from Expenses (already updated by rreading_amazon_csv_to_expenses(expenses_df))
def calculating_operational_expenses(df_expenses, year, quarter=None, month=None):

    # Filter data by year, quarter, or month
    df_expenses_filtered = filtering_by_year_quarter_month(df_expenses, year, quarter, month)

    total_operational_expenses = 0

    # Iterate through expenses and calculate totals
    for index, row in df_expenses_filtered.iterrows():
        if row['expense_type'] in operational_expenses:
            total_operational_expenses += row['total_transaction']
    
    return total_operational_expenses

# Function that will calculate Other Income from Income (already updated by reading_amazon_csv_to_income(income_df, inventory_df))
def calculating_other_income(df_income, year, quarter=None, month=None):

    # Filter data by year, quarter, or month
    df_income_filtered = filtering_by_year_quarter_month(df_income, year, quarter, month)

    total_other_income = 0

    for index, row in df_income_filtered.iterrows():
        if row['income_type'] in other_income:
            total_other_income += row['total_transaction']

    return total_other_income

# ---------------------------------REPORT GENERATION LOGIC -------------------------------------

# Function that will filter Data Frames according to the Period of time, Year, Quarter or Month that the User provides
def filtering_by_year_quarter_month(df, year, quarter=None, month=None):

    # Filter data by year, quarter, or month
    df_filtered = df[df['date'].dt.year == year]

    if quarter is not None:
        df_filtered = df_filtered[df_filtered['date'].dt.quarter == quarter]
    
    if month is not None:
        df_filtered = df_filtered[df_filtered['date'].dt.month == month]

    return df_filtered

# Income Statement Function that will get the Income Statement out of the period the User enters
def income_statement(df_income, df_expenses, year, quarter=None, month=None):

    # Filter data by year, quarter, or month
    df_income_filtered = filtering_by_year_quarter_month(df_income, year, quarter, month)

    total_revenue = 0
    cogs = 0
    total_operational_expenses = calculating_operational_expenses(df_expenses, year, quarter, month)
    total_other_income = calculating_other_income(df_income, year, quarter, month)

    # Iterate through sales and calculate totals
    for _, sale in df_income_filtered.iterrows():
        sku = sale['sku']
        quantity_sold = sale['quantity']
        unit_price = sale['unit_price']

        # Calculate revenue and COGS
        total_revenue += unit_price * quantity_sold
        cogs += calculate_cogs(sku, quantity_sold)

        # Update the inventory after calculating COGS
        update_inventory(sku, quantity_sold)  # Now correctly passing the arguments
        
        total_operational_expenses += sale['total_amazon_cost'] if not pd.isna(sale['total_amazon_cost']) else 0        

    gross_margin = total_revenue - cogs
    operational_margin = gross_margin - total_operational_expenses
    taxes = 0  # Adjust taxes based on your logic
    net_profit = operational_margin - taxes

        # Handle cases where total_revenue is zero to avoid division by zero errors
    if total_revenue != 0:
        gross_margin_percentage = (gross_margin / total_revenue) * 100
        net_profit_percentage = (net_profit / total_revenue) * 100
    else:
        gross_margin_percentage = 0  # or None, based on your preference
        net_profit_percentage = 0  # or None

    # Return a dictionary with the calculated values
    income_statement = {
        'total_revenue': total_revenue,
        'cogs': cogs,
        'gross_margin': gross_margin,
        'gross_margin_%': gross_margin_percentage,
        'other_income': total_other_income,
        'total_operational_expenses': total_operational_expenses,
        'operational_margin': operational_margin,
        'taxes': taxes,
        'net_profit': net_profit,
        'net_profit_%': net_profit_percentage
    }

    return income_statement

# Function to calculate current and previous period income statements and automatically generate labels
def generate_comparative_income_statement(df_income, df_expenses, year, quarter=None, month=None):
    # Calculate current period income statement
    current_period = income_statement(df_income, df_expenses, year, quarter, month)

    # Generate current period label
    current_period_label = generate_period_label(year, quarter, month)

    # Calculate previous period based on provided data
    if month:
        previous_month = month - 1 if month > 1 else 12
        previous_year = year if month > 1 else year - 1
        previous_period_label = generate_period_label(previous_year, month=previous_month)
        previous_period = income_statement(df_income, df_expenses, previous_year, None, previous_month)
    elif quarter:
        previous_quarter = quarter - 1 if quarter > 1 else 4
        previous_year = year if quarter > 1 else year - 1
        previous_period_label = generate_period_label(previous_year, quarter=previous_quarter)
        previous_period = income_statement(df_income, df_expenses, previous_year, previous_quarter)

    else:
        previous_year = year - 1
        previous_period_label = generate_period_label(previous_year)
        previous_period = income_statement(df_income, df_expenses, previous_year)

    return current_period, previous_period, current_period_label, previous_period_label
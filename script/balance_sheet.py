import pandas as pd
import math

from data import *
from inventory import *

def updating_inventory_with_sales_period(year, quarter=None):

    df_income = pd.read_csv('data/Income.csv')
    df_expenses = pd.read_csv('data/Expenses.csv')

    df_income = convert_date(df_income)
    df_expenses = convert_date(df_expenses)

    df_inventory = create_inventory_per_period(df_expenses, year, quarter)

    # Filter data by year, quarter, or month
    df_income_filtered = filter_transactions_before_period(df_income, year, quarter)

    # Iterate through sales and calculate totals
    for _, sale in df_income_filtered.iterrows():
        sku = sale['sku']
        quantity_sold = sale['quantity']

        # Update the inventory after calculating COGS
        update_inventory(df_inventory, sku, quantity_sold)  # Now correctly passing the arguments

    
    return df_inventory

def calculating_inventory_value_period(df_inventory):

    inventory_value = getting_inventory_value(df_inventory)

    return inventory_value

import pandas as pd
import math

from data import *
from inventory import *
from utils import *

def calculating_inventory_value(df_expenses, df_income, df_inventory, year, quarter=None, month=None):

    # Filter purchases and sales by date range
    df_expenses_filtered = filtering_by_year_quarter_month(df_expenses, year, quarter, month)
    df_income_filtered = filtering_by_year_quarter_month(df_income, year, quarter, month)

    # Initialize inventory dictionary to track quantities of each SKU
    inventory_tracker = {}

    # Process purchases (adding to inventory)
    for _, row in df_expenses_filtered.iterrows():

        if (row['expense_type'] == 'purchase_inventory') and (row['sku'] == 162593.0):

            sku = row['sku']

            if sku not in inventory_tracker:
                inventory_tracker[sku] = {
                    'quantity': 0,
                    'total_cogs': 0
                }

            print(row['quantity'])
            batch = row['batch']
            cogs = float(df_inventory[df_inventory['batch'] == batch]['total_cogs'].values[0])
            print(cogs)

            inventory_tracker[sku]['quantity'] += row['quantity']
            inventory_tracker[sku]['total_cogs'] += cogs * row['quantity']

    print('dsdsdsdsd', inventory_tracker)

    # Process sales (subtracting from inventory)
    for _, income_row in df_income_filtered.iterrows():

        if income_row['sku'] in inventory_tracker:

            inventory_tracker[income_row['sku']]['quantity'] -= income_row['quantity']
        
        if income_row['income_type'] == 'Refund':

            refunded_sku = getting_sku_with_order_id(df_income_filtered, income_row['order_id'])
            unit_price = getting_unit_price_with_order_id(df_income_filtered, income_row['order_id'])

            total_transaction = abs(income_row['total_transaction'])

            # Calculate how many items were refunded
            refunded_quantity = total_transaction / unit_price  # Don't round yet

            # If the refunded quantity is not an exact number, round up to get the full item count
            if refunded_quantity % 1 != 0:
                refunded_quantity = math.ceil(refunded_quantity)
            
            # Add refunded quantity back to inventory (without subtracting 1)
            inventory_tracker[refunded_sku]['quantity'] += int(refunded_quantity)


    return inventory_tracker



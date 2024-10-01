# inventory.py

import pandas as pd
from data import df_inventory
from utils import *

# Adding Inventroy from Purchasing_inventory Expenses from expenses.csv
def add_inventory(expenses_df):   #FIFO
    for index, row in expenses_df.iterrows():
        if row['expense_type'] == 'purchase_inventory':

            # Find additional expenses related to this batch; SHIPPING and IMPORT DUTIES
            batch_shipping = pd.to_numeric(expenses_df[
                (expenses_df['expense_type'] == 'shipping_supplier') &
                (expenses_df['batch'] == row['batch'])
            ]['total_transaction'], errors='coerce').sum()

            batch_import_duties = pd.to_numeric(expenses_df[
                (expenses_df['expense_type'] == 'import_taxes') &
                (expenses_df['batch'] == row['batch'])
            ]['total_transaction'], errors='coerce').sum()

            # Total quantity per batch
            total_quantity_batch = expenses_df[
                (expenses_df['batch'] == row['batch']) &
                (expenses_df['expense_type'] == 'purchase_inventory')                
            ]['quantity'].sum()

            # Total additional costs for this batch
            total_additional_costs = batch_shipping + batch_import_duties

            # Calculate total COGS per BATCH and divide it to each item to get unit_price
            unit_price = row['unit_price'] + total_additional_costs / total_quantity_batch

            inventory_row = {
                'date': row['date'],
                'sku': row['sku'],
                'batch': row['batch'],
                'quantity': row['quantity'],
                'unit_price': row['unit_price'],
                'total_transaction': row['total_transaction'],
                'ean': row['ean'],
                'asin': row['asin'],
                'supplier': row['channel'],
                'total_cogs': unit_price    # Total COGS per unit (shipping and taxes) + the unit_price
            }
            
            df_inventory.loc[len(df_inventory)] = inventory_row

# UPDATING INVENTORY AFTER A SALE GOING TROUGH BATCHES IN INVENTORY
def update_inventory(df_inventory, sku, quantity_sold):

    remaining_quantity = quantity_sold

    # Filter inventory by SKU and sort by batch (FIFO)
    sku_inventory = df_inventory[df_inventory['sku'] == sku].sort_values(by='batch')

    for index, row in sku_inventory.iterrows():

        if remaining_quantity == 0:
            break

        available_quantity = row['quantity']

        if available_quantity <= remaining_quantity:
            remaining_quantity -= available_quantity
            df_inventory.at[index, 'quantity'] = 0
        else:
            df_inventory.at[index, 'quantity'] -= remaining_quantity
            remaining_quantity = 0

def update_inventory_refunded(income_df, inventory_df, order_id):

    df_inventory = inventory_df

    for index, row in income_df.iterrows():

        # Looking for rows with same order_id to change payment_status to REFUNDED
        if (row['order_id'] == order_id) and (row['payment_status'] == 'completed'):
            income_df.at[index, 'payment_status'] = 'REFUNDED'
            sku = income_df.at[index, 'sku']
            date = income_df.at[index, 'date']
            quantity = income_df.at[index, 'quantity']
            
            for index, row in df_inventory.iterrows():
                if (row['sku'] == sku) and (row['date'] <= date) and (quantity > 0):
                    df_inventory.at[index, 'quantity'] += quantity
                    quantity -= quantity
    
    
    return income_df, df_inventory

# Function to update inventory by reducing the quantity when faulty items are RETURNED from Amazon in Amazon.csv to Inventory df
def update_inventory_after_fault(sku, quantity_to_reduce, inventory_df):

    quantity_remaining = quantity_to_reduce

    # Find the SKU in inventory and reduce the quantity (FIFO logic can be applied if needed)
    for index, row in inventory_df.iterrows():
        if (row['sku'] == sku) and (quantity_remaining > 0):
            inventory_df.at[index, 'quantity'] -= quantity_to_reduce
            quantity_remaining -= quantity_to_reduce
            print('SKUUUUUUUUUUUUUUUUU',row['sku'], row['quantity'])
    
    return inventory_df

def getting_sku_with_order_id(df_income, order_id):

    for index, row in df_income.iterrows():

        if row['income_type'] == 'Sales' and row['order_id'] == order_id:

            sku = row['sku']
            unit_price = row['unit_price']

    return sku

def getting_unit_price_with_order_id(df_income, order_id):

    for index, row in df_income.iterrows():

        if row['income_type'] == 'Sales' and row['order_id'] == order_id:

            unit_price = row['unit_price']

    return unit_price

def getting_inventory_value(df_inventory):

    total_cogs = 0

    for _, row in df_inventory.iterrows():
        total_cogs += row['quantity'] * row['total_cogs']

    return total_cogs

def create_inventory_per_period(expenses_df, year, quarter=None):   #FIFO
    
    df_expenses = convert_date(expenses_df)
    df_filtered_expenses = filter_transactions_before_period(df_expenses, year, quarter)

    df_inventory_period = pd.DataFrame(columns=['date','sku','batch','quantity','unit_price','total_transaction','ean','asin','supplier','total_cogs'])
    
    for index, row in df_filtered_expenses.iterrows():
        if row['expense_type'] == 'purchase_inventory':

            # Find additional expenses related to this batch; SHIPPING and IMPORT DUTIES
            batch_shipping = pd.to_numeric(df_filtered_expenses[
                (df_filtered_expenses['expense_type'] == 'shipping_supplier') &
                (df_filtered_expenses['batch'] == row['batch'])
            ]['total_transaction'], errors='coerce').sum()

            batch_import_duties = pd.to_numeric(df_filtered_expenses[
                (df_filtered_expenses['expense_type'] == 'import_taxes') &
                (df_filtered_expenses['batch'] == row['batch'])
            ]['total_transaction'], errors='coerce').sum()

            # Total quantity per batch
            total_quantity_batch = df_filtered_expenses[
                (df_filtered_expenses['batch'] == row['batch']) &
                (df_filtered_expenses['expense_type'] == 'purchase_inventory')                
            ]['quantity'].sum()

            # Total additional costs for this batch
            total_additional_costs = batch_shipping + batch_import_duties

            # Calculate total COGS per BATCH and divide it to each item to get unit_price
            unit_price = row['unit_price'] + total_additional_costs / total_quantity_batch

            inventory_row = {
                'date': row['date'],
                'sku': row['sku'],
                'batch': row['batch'],
                'quantity': row['quantity'],
                'unit_price': row['unit_price'],
                'total_transaction': row['total_transaction'],
                'ean': row['ean'],
                'asin': row['asin'],
                'supplier': row['channel'],
                'total_cogs': unit_price    # Total COGS per unit (shipping and taxes) + the unit_price
            }
            
            df_inventory_period.loc[len(df_inventory_period)] = inventory_row

    return df_inventory_period


import pandas as pd
import math

from data import *
from inventory import *
from income_statement import *

def reading_amazon_csv_to_expenses_period(df_expenses_period):
    
    df_amazon = pd.read_csv('data/Amazon.csv')
    df_amazon = convert_date(df_amazon)
    
    # Start with the current length of the expenses DataFrame for entry ID tracking
    current_expense_id = len(df_expenses_period)

    # Looking for Operational Costs from file and adding it to df_expenses
    for _, row in df_amazon.iterrows():

        if row['Product Details'] == 'Inbound Transportation Charge':

            df_expenses_period.loc[len(df_expenses_period)] = {
                'expense_entry_id': current_expense_id,
                'date': row['date'],  # Date from Amazon CSV
                'expense_type': row['Product Details'],  # Product Details mapped to expense_type
                'unit_price': abs(row['Total (AUD)']),  # Total (AUD) mapped to unit_price
                'quantity': 1,  # Quantity is set to 1 as required
                'total_transaction': abs(row['Total (AUD)']),  # Total (AUD) for total_transaction
                'payment_type': 'cash',
                'payment_status': 'completed',
                'description': row['Product Details']  # Description similar to expense_type
            }

            current_expense_id += 1

        if row['Product Details'] == 'FBA storage fee':

            df_expenses_period.loc[len(df_expenses_period)] = {
                'expense_entry_id': current_expense_id,
                'date': row['date'],  # Date from Amazon CSV
                'expense_type': row['Product Details'],  # Product Details mapped to expense_type
                'unit_price': abs(row['Total (AUD)']),  # Total (AUD) mapped to unit_price
                'quantity': 1,  # Quantity is set to 1 as required
                'total_transaction': abs(row['Total (AUD)']),  # Total (AUD) for total_transaction
                'payment_type': 'cash',
                'payment_status': 'completed',
                'description': row['Product Details']  # Description similar to expense_type
            }

            current_expense_id += 1

        if row['Product Details'] == 'FBA Return Fee':

            df_expenses_period.loc[len(df_expenses_period)] = {
                'expense_entry_id': current_expense_id,
                'date': row['date'],  # Date from Amazon CSV
                'expense_type': row['Product Details'],  # Product Details mapped to expense_type
                'unit_price': abs(row['Total (AUD)']),  # Total (AUD) mapped to unit_price
                'quantity': 1,  # Quantity is set to 1 as required
                'total_transaction': abs(row['Total (AUD)']),  # Total (AUD) for total_transaction
                'payment_type': 'cash',
                'payment_status': 'completed',
                'description': row['Product Details']  # Description similar to expense_type
            }

            current_expense_id += 1

    return df_expenses_period

def updating_inventory_with_sales_period(year, quarter=None):

    df_income = pd.read_csv('data/Income.csv')
    df_expenses = pd.read_csv('data/Expenses.csv')

    df_income = convert_date(df_income)
    df_expenses = convert_date(df_expenses)

    df_inventory = create_inventory_per_period(df_expenses, year, quarter)

    # Filter data by year, quarter, or month
    df_income_filtered = filter_transactions_before_period(df_income, year, quarter)
    df_expenses_filtered = filter_transactions_before_period(df_expenses, year, quarter)

    # Iterate through sales and calculate totals
    for _, sale in df_income_filtered.iterrows():
        sku = sale['sku']
        quantity_sold = sale['quantity']

        # Update the inventory after calculating COGS
        update_inventory(df_inventory, sku, quantity_sold)  # Now correctly passing the arguments

    
    return df_income_filtered, df_expenses_filtered, df_inventory

def calculating_inventory_value_period(df_inventory):

    inventory_value = getting_inventory_value(df_inventory)

    return inventory_value

def updating_income_inventory_with_amazon(df_income_period, df_inventory_period, year, quarter=None):

    df_amazon = pd.read_csv('data/Amazon.csv')
    df_amazon = convert_date(df_amazon)
    
    df_amazon_period = filter_transactions_before_period(df_amazon, year, quarter)

    # Creating variable to generate entry_id according to the lenght of the DataFrame
    current_income_id = len(df_income_period) + 1

    for index, row in df_amazon_period.iterrows():

        # Going through Sales and updating payment_status from Pending to Completed for those that Amazon paid, checking by Order Id
        if (row['Transaction type'] == 'Order payment') and (row['Transaction Status'] == 'Released'):
            df_income_period = updating_payment_status(df_income_period, row['Order ID'])

        # Looking for Transaction Type - Order Payment for registering sales
        if row['Transaction type'] == 'Paid to Amazon | Seller repayment':
            df_income_period.loc[len(df_income_period)] = {
                'order_entry_id': current_income_id,
                'income_type': 'Amazon Repayment',
                'date': row['date'],
                'channel': 'Amazon',
                'quantity': 1,
                'unit_price': row['Total (AUD)'],
                'total_transaction': row['Total (AUD)'],
                'payment_type': 'cash',
                'payment_status': 'completed',
                'description': row['Product Details']
            }

            current_income_id += 1
        
        # Looking for Transaction Type - Other - Reimbursement - which is a return of a faulty item so we have to remove it from Inventory
        if row['Product Details'] == 'FBA Inventory Reimbursement':

            order_id = row['Order ID']

            sku = getting_sku_with_order_id(df_income, order_id)

            # Locate the row where both 'sku' and 'order_id' match, and update the 'payment_status'
            df_income_period.loc[(df_income_period['sku'] == sku) & (df_income_period['order_id'] == order_id), 'payment_status'] = 'FAULTY'


            # Updating the Inventory to remove the FAULTY ITEMS FROM INVENTORY
            df_inventory_period = update_inventory_after_fault(sku, 1, df_inventory_period)

            df_income_period.loc[len(df_income_period)] = {
                'order_entry_id': current_income_id,
                'order_id': row['Order ID'],
                'income_type': 'Amazon Repayment for faulty Item',
                'date': row['date'],
                'channel': 'Amazon',
                'quantity': 1,
                'unit_price': row['Total (AUD)'],
                'total_transaction': row['Total (AUD)'],
                'payment_type': 'cash',
                'payment_status': 'completed',
                'description': row['Product Details']
            }

            current_income_id += 1

        # Looking for Transaction Type - REFUNDS - and making a sale for the same ORDER_ID in negative and updating the inventory
        if row['Transaction type'] == 'Refund':

            # Look in income_df for order_id and change the payment_status to "Refunded"
            df_income_period, df_inventory_period = update_inventory_refunded(df_income_period, df_inventory_period, row['Order ID'])

            df_income_period.loc[len(df_income_period)] = {
                'order_entry_id': current_income_id,
                'order_id': row['Order ID'],
                'income_type': 'Refund',
                'date': row['date'],
                'channel': 'Amazon',
                'quantity': 1,
                'unit_price': row['Total (AUD)'],
                'total_transaction': row['Total (AUD)'],
                'payment_type': 'cash',
                'payment_status': 'completed',
                'description': row['Product Details']
            }

            current_income_id += 1

    return df_income_period, df_inventory_period

# def calculating_cash_receivable(df_income_period, df_expenses_period):

#     account_receivable = 0
#     cash = 0

#     for _, row in df_income_period.iterrows():

#         if row['payment_status'] == 'pending':
#             account_receivable += row['total_transaction']
#         else:
#             cash += row['total_transaction']

#     print('CASH',cash)
#     print('account', account_receivable)

#     for _, row in df_expenses_period.iterrows():

#         if row

#     return cash, account_receivable

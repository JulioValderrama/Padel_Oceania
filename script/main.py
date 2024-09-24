import pandas as pd

# Importing other modules
from data import df_income, df_expenses
from income_statement import updating_payment_status, generate_comparative_income_statement
from inventory import *
from utils import *

from pdf_export import create_comparative_table, export_to_pdf  # Importing functions from the pdf_export module

# ---------------------------------READING, CLEANIGN AND UPLOADING DATA FROM CSV -------------------------------------

# Function to read Amazon.csv and update Expenses for OPERATIONAL EXPENSES
def reading_amazon_csv_to_expenses(expenses_df):
    
    df_amazon = pd.read_csv('data/Amazon.csv')
    df_amazon = convert_date(df_amazon)
    
    # Start with the current length of the expenses DataFrame for entry ID tracking
    current_expense_id = len(expenses_df)

    # Looking for Operational Costs from file and adding it to df_expenses
    for index, row in df_amazon.iterrows():

        if row['Product Details'] == 'Inbound Transportation Charge':

            expenses_df.loc[len(expenses_df)] = {
                'expense_entry_id': current_expense_id,
                'date': row['date'],  # Date from Amazon CSV
                'expense_type': row['Product Details'],  # Product Details mapped to expense_type
                'unit_price': abs(row['Total (AUD)']),  # Total (AUD) mapped to unit_price
                'quantity': 1,  # Quantity is set to 1 as required
                'total_transaction': abs(row['Total (AUD)']),  # Total (AUD) for total_transaction
                'description': row['Product Details']  # Description similar to expense_type
            }

            current_expense_id += 1

        if row['Product Details'] == 'FBA storage fee':

            expenses_df.loc[len(expenses_df)] = {
                'expense_entry_id': current_expense_id,
                'date': row['date'],  # Date from Amazon CSV
                'expense_type': row['Product Details'],  # Product Details mapped to expense_type
                'unit_price': abs(row['Total (AUD)']),  # Total (AUD) mapped to unit_price
                'quantity': 1,  # Quantity is set to 1 as required
                'total_transaction': abs(row['Total (AUD)']),  # Total (AUD) for total_transaction
                'description': row['Product Details']  # Description similar to expense_type
            }

            current_expense_id += 1

        if row['Product Details'] == 'FBA Return Fee':

            expenses_df.loc[len(expenses_df)] = {
                'expense_entry_id': current_expense_id,
                'date': row['date'],  # Date from Amazon CSV
                'expense_type': row['Product Details'],  # Product Details mapped to expense_type
                'unit_price': abs(row['Total (AUD)']),  # Total (AUD) mapped to unit_price
                'quantity': 1,  # Quantity is set to 1 as required
                'total_transaction': abs(row['Total (AUD)']),  # Total (AUD) for total_transaction
                'description': row['Product Details']  # Description similar to expense_type
            }

            current_expense_id += 1

    return expenses_df

# Function to go through Amazon.csv and UPDATE Income DataFrame for registering other TYPES OF INCOMES from Amazon like repayment or FBA Inventory Reimbursement
def reading_amazon_csv_to_income(income_df, inventory_df):

    df_amazon = pd.read_csv('data/Amazon.csv')
    df_amazon = convert_date(df_amazon)

    # Creating variable to generate entry_id according to the lenght of the DataFrame
    current_income_id = len(income_df) + 1

    for index, row in df_amazon.iterrows():

        # Going through Sales and updating payment_status from Pending to Completed for those that Amazon paid, checking by Order Id
        if row['Transaction type'] == 'Order payment':
            income_df = updating_payment_status(income_df, row['Order ID'])

        # Looking for Transaction Type - Order Payment for registering sales
        if row['Transaction type'] == 'Paid to Amazon | Seller repayment':
            income_df.loc[len(income_df)] = {
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

            sku = int(row['Order ID'])

            # Updating the Inventory to remove the FAULTY ITEMS FROM INVENTORY
            inventory_df = update_inventory_after_fault(sku, 1, inventory_df)

            income_df.loc[len(income_df)] = {
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
            income_df, inventory_df = update_inventory_refunded(income_df, inventory_df, row['Order ID'])

            income_df.loc[len(income_df)] = {
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

    return income_df, inventory_df

#  ---------------------------- WORK FLOW --------------------------------------------------------------------------

# Populate the inventory with purchase data from expenses.csv
add_inventory(df_expenses)

# Updating the Expenses with OPERATIONAL EXPENSES from Amazon.csv
df_expenses = reading_amazon_csv_to_expenses(df_expenses)

# Updating the
df_income, df_inventory = reading_amazon_csv_to_income(df_income, df_inventory)

# Generate comparative income statement for Q2 2024
current_period, previous_period, current_period_label, previous_period_label = generate_comparative_income_statement(df_income, df_expenses, 2024, 3)

# Create the table and export to PDF (period labels generated automatically)
create_comparative_table(current_period, previous_period, current_period_label, previous_period_label)
export_to_pdf(current_period, previous_period, current_period_label, previous_period_label)

df_income.to_csv('resultInc.csv', index=False)
df_inventory.to_csv('resultInven.csv', index=False)
df_expenses.to_csv('resultExp.csv', index=False)


import pandas as pd
from pdf_export import create_comparative_table, export_to_pdf  # Importing functions from the pdf_export module

# Read all CSV files and create DataFrames
df_income = pd.read_csv('data/Income.csv')
df_expenses = pd.read_csv('data/Expenses.csv')
df_liabilities = pd.read_csv('data/Liabilities.csv')

# Display all rows
pd.set_option('display.max_rows', None)
# Display all columns
pd.set_option('display.max_columns', None)

# Inventory DataFrame
df_inventory = pd.DataFrame(columns=['date','sku','batch','quantity','unit_price','total_transaction','ean','asin','supplier','total_cogs'])

# Financial DataFrames for future usage
df_income_statement = pd.DataFrame(columns=['date','total_revenue','total_cogs','total_operational_expenses', 'gross_margin','operational_margin','taxes','net_profit'])

other_income = [
    'Amazon Repayment',
    'Amazon Repayment for faulty Item'
]

operational_expenses = [
    'Administrative Expense',
    'FBA storage fee',
    'Inbound Transportation Charge',
    'FBA Return Fee'
]

# ---------------------------------READING, CLEANIGN AND UPLOADING DATA FROM CSV -------------------------------------

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

# Cleaning column DATE and converting it to format DateTime
def convert_date(df):
    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
    return df

# UPDATING INVENTORY AFTER A SALE GOING TROUGH BATCHES IN INVENTORY
def update_inventory(sku, quantity_sold):
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

# Function to calculate the COGS
def calculate_cogs(sku, quantity_sold):
    cogs = 0
    remaining_quantity = quantity_sold
    
    # Filter inventory by SKU and sort by batch (FIFO)
    sku_inventory = df_inventory[df_inventory['sku'] == sku].sort_values(by='batch')
    
    for _, row in sku_inventory.iterrows():
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
        
        # Looking for Transaction Type - Other - Reimbursement - 
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

# Function to update the payment_status from PENDING to COMPLETED for those sales credited and PAID from Amazon
def updating_payment_status(income_df, order_id):

    for index, row in income_df.iterrows():

        # Looking for rows with PENDING status and changing it to COMPLETED
        if (row['order_id'] == order_id) and (row['payment_status'] == 'pending'):
            income_df.at[index, 'payment_status'] = 'completed'
    
    
    return income_df

# Function to update inventory by reducing the quantity when faulty items are RETURNED from Amazon
def update_inventory_after_fault(sku, quantity_to_reduce, inventory_df):

    quantity_remaining = quantity_to_reduce

    # Find the SKU in inventory and reduce the quantity (FIFO logic can be applied if needed)
    for index, row in inventory_df.iterrows():
        if (row['sku'] == sku) and (quantity_remaining > 0):
            inventory_df.at[index, 'quantity'] -= quantity_to_reduce
            quantity_remaining -= quantity_to_reduce
    
    return inventory_df

def calculating_operational_expenses(df_expenses, year, quarter=None, month=None):

    # Filter data by year, quarter, or month
    df_expenses_filtered = filtering_by_year_quarter_month(df_expenses, year, quarter, month)

    total_operational_expenses = 0

    # Iterate through expenses and calculate totals
    for index, row in df_expenses_filtered.iterrows():
        if row['expense_type'] in operational_expenses:
            total_operational_expenses += row['total_transaction']
    
    return total_operational_expenses

def calculating_other_income(df_income, year, quarter=None, month=None):

    # Filter data by year, quarter, or month
    df_income_filtered = filtering_by_year_quarter_month(df_income, year, quarter, month)

    total_other_income = 0

    for index, row in df_income_filtered.iterrows():
        if row['income_type'] in other_income:
            total_other_income += row['total_transaction']

    return total_other_income

def filtering_by_year_quarter_month(df, year, quarter=None, month=None):

    # Filter data by year, quarter, or month
    df_filtered = df[df['date'].dt.year == year]

    if quarter is not None:
        df_filtered = df_filtered[df_filtered['date'].dt.quarter == quarter]
    
    if month is not None:
        df_filtered = df_filtered[df_filtered['date'].dt.month == month]

    return df_filtered

# ---------------------------------REPORT GENERATION LOGIC -------------------------------------

def format_value(value):
    return f'{float(value):,.2f}'  # Ensure we restrict to 2 decimal places

# Income Statement Function
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

    # Return a dictionary with the calculated values
    income_statement = {
        'total_revenue': format_value(total_revenue),
        'cogs': format_value(cogs),
        'gross_margin': format_value(gross_margin),
        'other_income': format_value(total_other_income),
        'total_operational_expenses': format_value(total_operational_expenses),
        'operational_margin': format_value(operational_margin),
        'taxes': format_value(taxes),
        'net_profit': format_value(net_profit)
    }

        # Iterate through the dictionary and print each key and its corresponding value
    for key, value in income_statement.items():
        print(f"{key}: {value}")

    return income_statement

# Function to generate period labels dynamically
def generate_period_label(year, quarter=None, month=None):
    if month:
        # Convert month number to month name
        month_name = pd.to_datetime(f'{year}-{month}-01').strftime('%B')
        return f'{month_name} {year}'
    elif quarter:
        return f'Q{quarter} {year}'
    else:
        return str(year)

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


#  ---------------------------- WORK FLOW --------------------------------------------------------------------------

# Formatting colum DATE into a DateTime object
df_income = convert_date(df_income)
df_expenses = convert_date(df_expenses)
df_liabilities = convert_date(df_liabilities)

# Populate the inventory with purchase data from expenses.csv
add_inventory(df_expenses) 

# Updating the Expenses with OPERATIONAL EXPENSES from Amazon.csv
df_expenses = reading_amazon_csv_to_expenses(df_expenses)
df_income, df_inventory = reading_amazon_csv_to_income(df_income, df_inventory)

# Generate comparative income statement for Q2 2024
current_period, previous_period, current_period_label, previous_period_label = generate_comparative_income_statement(df_income, df_expenses, 2024, month=6)

# Create the table and export to PDF (period labels generated automatically)
create_comparative_table(current_period, previous_period, current_period_label, previous_period_label)
export_to_pdf(current_period, previous_period, current_period_label, previous_period_label)

df_income.to_csv('resultInc.csv', index=False)
df_inventory.to_csv('resultInven.csv', index=False)
df_expenses.to_csv('resultExp.csv', index=False)
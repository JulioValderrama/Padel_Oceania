import pandas as pd

# Read all CSV files and create DataFrames
df_income = pd.read_csv('data/Income.csv')
df_expenses = pd.read_csv('data/Expenses.csv')
df_liabilities = pd.read_csv('data/Liabilities.csv')

# Display all rows
pd.set_option('display.max_rows', None)
# Display all columns
pd.set_option('display.max_columns', None)

# Inventory DataFrame
df_inventory = pd.DataFrame(columns=['sku','batch','quantity','unit_price','total_transaction','ean','asin','supplier','total_cogs'])

# Financial DataFrames for future usage
df_income_statement = pd.DataFrame(columns=['date','total_revenue','total_cogs','total_operational_expenses', 'gross_margin','operational_margin','taxes','net_profit'])


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
            cogs += available_quantity * row['unit_price']
            remaining_quantity -= available_quantity
        else:
            cogs += remaining_quantity * row['unit_price']
            remaining_quantity = 0
    
    return cogs

def reading_amazon_csv_to_expenses(expenses_df):

    inbound_transportation_charge = 0
    fba_storage_fee = 0
    fba_return_fee = 0
    
    df_amazon = pd.read_csv('data/Amazon.csv')
    df_amazon = convert_date(df_amazon)
    
    # Start with the current length of the expenses DataFrame for entry ID tracking
    current_expense_id = len(expenses_df)

    # Looking for Operational Costs from file and adding it to df_expenses
    for index, row in df_amazon.iterrows():

        if row['Product Details'] == 'Inbound Transportation Charge':
            inbound_transportation_charge += row['Total (AUD)']

            expenses_df.loc[len(expenses_df)] = {
                'expense_entry_id': current_expense_id,
                'date': row['date'],  # Date from Amazon CSV
                'expense_type': row['Product Details'],  # Product Details mapped to expense_type
                'unit_price': row['Total (AUD)'],  # Total (AUD) mapped to unit_price
                'quantity': 1,  # Quantity is set to 1 as required
                'total_transaction': row['Total (AUD)'],  # Total (AUD) for total_transaction
                'description': row['Product Details']  # Description similar to expense_type
            }

            current_expense_id += 1

        if row['Product Details'] == 'FBA storage fee':
            inbound_transportation_charge += row['Total (AUD)']

            expenses_df.loc[len(expenses_df)] = {
                'expense_entry_id': current_expense_id,
                'date': row['date'],  # Date from Amazon CSV
                'expense_type': row['Product Details'],  # Product Details mapped to expense_type
                'unit_price': row['Total (AUD)'],  # Total (AUD) mapped to unit_price
                'quantity': 1,  # Quantity is set to 1 as required
                'total_transaction': row['Total (AUD)'],  # Total (AUD) for total_transaction
                'description': row['Product Details']  # Description similar to expense_type
            }

            current_expense_id += 1

        if row['Product Details'] == 'FBA Return Fee':
            inbound_transportation_charge += row['Total (AUD)']

            expenses_df.loc[len(expenses_df)] = {
                'expense_entry_id': current_expense_id,
                'date': row['date'],  # Date from Amazon CSV
                'expense_type': row['Product Details'],  # Product Details mapped to expense_type
                'unit_price': row['Total (AUD)'],  # Total (AUD) mapped to unit_price
                'quantity': 1,  # Quantity is set to 1 as required
                'total_transaction': row['Total (AUD)'],  # Total (AUD) for total_transaction
                'description': row['Product Details']  # Description similar to expense_type
            }

            current_expense_id += 1

    return expenses_df

def updating_payment_status(income_df, order_id):

    for index, row in income_df.iterrows():
        
        if (row['order_id'] == order_id) and (row['payment_status'] == 'pending'):
            income_df.at[index, 'payment_status'] = 'completed'
    
    
    return income_df


# ---------------------------------REPORT GENERATION LOGIC -------------------------------------

# Income Statement Function
def income_statement(df_income, year, quarter=None, month=None):

    # Filter data by year, quarter, or month
    df_filtered = df_income[df_income['date'].dt.year == year]

    if quarter:
        df_filtered = df_filtered[df_filtered['date'].dt.quarter == quarter]
    elif month:
        df_filtered = df_filtered[df_filtered['date'].dt.month == month]

    total_revenue = 0
    cogs = 0
    total_operational_expenses = 0

    # Iterate through sales and calculate totals
    for _, sale in df_filtered.iterrows():
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
    return {
        'total_revenue': total_revenue,
        'cogs': cogs,
        'total_operational_expenses': total_operational_expenses,
        'gross_margin': gross_margin,
        'operational_margin': operational_margin,
        'taxes': taxes,
        'net_profit': net_profit
    }


#  ---------------------------- WORK FLOW --------------------------------------------------------------------------

# Formatting colum DATE into a DateTime object
df_income = convert_date(df_income)
df_expenses = convert_date(df_expenses)
df_liabilities = convert_date(df_liabilities)

# Populate the inventory with purchase data
add_inventory(df_expenses) 

# Updating the Expenses with OPERATIONAL EXPENSES from Amazon.csv
df_expenses = reading_amazon_csv_to_expenses(df_expenses)

# Populate the inventory with purchase data
result = income_statement(df_income,2024)
print(result)
print(f"Total Revenue: {result['total_revenue']}, Total COGS: {result['cogs']}, Operational Expense: {result['total_operational_expenses']}, Net Income: {result['net_profit']}")


# # Export the DataFrame to a CSV file
# df_expenses.to_csv('1exported_expenses.csv', index=False)


#df_income = updating_payment_status (df_income, '249-4824839-9495848')

df_income = updating_payment_status(df_income, '249-4824839-9495848')

print(df_income)

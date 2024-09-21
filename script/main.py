import pandas as pd

# Read all CSV files and create DataFrames
df_income = pd.read_csv('data/Income.csv')
df_expenses = pd.read_csv('data/Expenses.csv')
df_liabilities = pd.read_csv('data/Liabilities.csv')

# Cleaning column DATE and converting it to format DateTime
def convert_date(df):
    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
    return df

df_income = convert_date(df_income)
df_expenses = convert_date(df_expenses)
df_liabilities = convert_date(df_liabilities)

# Inventory DataFrame
df_inventory = pd.DataFrame(columns=['sku','batch','quantity','unit_price','total_transaction','ean','asin','supplier','total_cogs'])

# Financial DataFrames for future usage
df_income_statement = pd.DataFrame(columns=['date','total_revenue','total_cogs','total_operational_expenses', 'gross_margin','operational_margin','taxes','net_profit'])


# ---------------------------------READING df_expenses AND CREATING INVENTORY OUT OF BUYING BATCHES FROM SUPPLIER -------------------------------------
def add_inventory(expenses_df):
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
        total_revenue += unit_price * quantity_sold
        cogs += calculate_cogs(sku, quantity_sold)
        total_operational_expenses += sale['total_amazon_cost'] if not pd.isna(sale['total_amazon_cost']) else 0

    gross_margin = total_revenue - cogs
    operational_margin = gross_margin - total_operational_expenses
    taxes = 0  # Adjust taxes based on your logic
    net_profit = operational_margin - taxes

    return total_revenue, cogs, total_operational_expenses, net_profit


revenue, expense, operational_expense, income = income_statement(2024,3)
print(f"Total Revenue: {revenue}, Total Expense: {expense}, Operational Expense: {operational_expense}, Net Income: {income}")


import pandas as pd


# Read all CSV files and create DataFrames
df_income = pd.read_csv('data/Income.csv')
df_expenses = pd.read_csv('data/Expenses.csv')
df_liabilities = pd.read_csv('data/Liabilities.csv')

# Cleaning columd DATE and converting it to format DateTime
def convertir_fecha(df):
    df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
    return df

df_income = convertir_fecha(df_income)
df_expenses = convertir_fecha(df_expenses)
df_liabilities = convertir_fecha(df_liabilities)

df_inventory = pd.DataFrame(columns=['sku','batch','quantity','unit_price','total_transaction','ean','asin','supplier','total_cogs'])

# FINANCIAL STATEMENTS

df_income_statement = pd.DataFrame(columns=['Date','total_revenue','total_cogs','total_operational_expenses', 'gross_margin','operational_margin','taxes','net_profit'])


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

add_inventory(df_expenses)

# ---------------------------------READING df_income  -------------------------------------

def income_statement(year, quarter=None, month=None):
    global df_income  # Usar la variable global

    total_revenue = 0
    cogs = 0
    total_operational_expenses = 0
    gross_margin = 0
    operational_margin = 0
    taxes = 0
    net_profit = 0

    df_income = df_income[df_income['date'].dt.year == year]

    # Filtering per quarter if provided
    if quarter:
        df_income = df_income[df_income['date'].dt.quarter == quarter]
    # Filetering per month if provided


    for index, sale in df_income.iterrows():
        sku = sale['sku']
        quantity_sold = sale['quantity']
        unit_price = sale['unit_price']

        total_revenue += unit_price * quantity_sold
        cogs += calculate_cogs(sku, quantity_sold)
        total_operational_expenses += sale['total_amazon_cost'] if not pd.isna(sale['total_amazon_cost']) else 0

    # Calculate varaibles
    gross_margin = total_revenue - cogs
    operational_margin = gross_margin - total_operational_expenses
    net_profit = operational_margin - taxes

    return total_revenue, cogs, total_operational_expenses, net_profit


# UPDATING INVENTORY AFTER A SALE GOING TROUGH BATCHES IN INVENTORY
def update_inventory(sku, quantity_sold):
    global df_inventory
    remaining_quantity = quantity_sold
    
    # Filter inventory by SKU and sort by batch (FIFO)
    sku_inventory = df_inventory[df_inventory['sku'] == sku].sort_values(by='batch')
    
    for index, row in sku_inventory.iterrows():
        if remaining_quantity == 0:
            break
        available_quantity = row['quantity']
        
        if available_quantity <= remaining_quantity:
            remaining_quantity -= available_quantity
            # Remove the sold quantity from inventory
            df_inventory.at[index, 'quantity'] = 0
        else:
            df_inventory.at[index, 'quantity'] -= remaining_quantity
            remaining_quantity = 0

# Function to calculate the COGS without updating inventory
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

revenue, expense, operational_expense, income = income_statement(2024,3)
print(f"Total Revenue: {revenue}, Total Expense: {expense}, Operational Expense: {operational_expense}, Net Income: {income}")


import pandas as pd

# Reading CSVs
def read_csv_files():
    df_income = pd.read_csv('data/Income.csv')
    df_expenses = pd.read_csv('data/Expenses.csv')
    df_liabilities = pd.read_csv('data/Liabilities.csv')
    return df_income, df_expenses, df_liabilities

# Function to configure display options
def configure_display_options():
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)

# Date formatting function
def convert_date(df):
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    return df

# Inventory handling
def add_inventory(expenses_df, df_inventory):
    for index, row in expenses_df.iterrows():
        if row['expense_type'] == 'purchase_inventory':
            add_inventory_for_batch(expenses_df, df_inventory ,row)
            
# Helper function for adding inventory for a batch
def add_inventory_for_batch(expenses_df, df_inventory, row):
    batch_shipping = get_batch_additional_costs(expenses_df, 'shipping_supplier', row['batch'])
    batch_import_duties = get_batch_additional_costs(expenses_df, 'import_taxes', row['batch'])
    
    total_quantity_batch = get_total_quantity(expenses_df, row['batch'])
    
    total_cogs = row['total_transaction'] + batch_shipping + batch_import_duties
    unit_cogs = total_cogs / total_quantity_batch
    
    # Create a new entry for inventory
    df_inventory.loc[len(df_inventory)] = {
        'sku': row['sku'],
        'batch': row['batch'],
        'quantity': row['quantity'],
        'unit_price': row['unit_price'],
        'total_transaction': row['total_transaction'],
        'ean': row['ean'],
        'asin': row['asin'],
        'supplier': row['channel'],
        'total_cogs': unit_cogs
    }

# Get total additional costs for a batch (shipping, import duties)
def get_batch_additional_costs(expenses_df, expense_type, batch):
    return pd.to_numeric(
        expenses_df[(expenses_df['expense_type'] == expense_type) & (expenses_df['batch'] == batch)]['total_transaction'], 
        errors='coerce'
    ).sum()

# Get total quantity for a batch
def get_total_quantity(expenses_df, batch):
    return expenses_df[(expenses_df['batch'] == batch) & (expenses_df['expense_type'] == 'purchase_inventory')]['quantity'].sum()

# Income statement generation
def income_statement(df_income, year):
    total_revenue, total_operational_expenses, cogs = 0, 0, 0
    for _, sale in df_income.iterrows():
        unit_price = sale['unit_price']
        quantity_sold = sale['quantity']
        sku = sale['sku']
        
        total_revenue += unit_price * quantity_sold
        cogs += calculate_cogs(sku, quantity_sold)
        total_operational_expenses += sale['total_amazon_cost'] if not pd.isna(sale['total_amazon_cost']) else 0
    
    gross_margin = total_revenue - cogs
    operational_margin = gross_margin - total_operational_expenses
    taxes = calculate_taxes(operational_margin)
    net_profit = operational_margin - taxes
    
    return {
        'total_revenue': total_revenue,
        'cogs': cogs,
        'total_operational_expenses': total_operational_expenses,
        'gross_margin': gross_margin,
        'operational_margin': operational_margin,
        'taxes': taxes,
        'net_profit': net_profit
    }

# Calculate COGS for a given SKU
def calculate_cogs(sku, quantity_sold):
    # Logic for calculating COGS based on inventory
    pass

# Calculate taxes based on operational margin
def calculate_taxes(operational_margin):
    # Add your tax logic here
    return 0  # Placeholder for tax logic

# Main workflow
def main():
    configure_display_options()
    df_income, df_expenses, df_liabilities = read_csv_files()

    # Date formatting
    df_income = convert_date(df_income)
    df_expenses = convert_date(df_expenses)
    df_liabilities = convert_date(df_liabilities)

    df_inventory = pd.DataFrame(columns=['sku','batch','quantity','unit_price','total_transaction','ean','asin','supplier','total_cogs'])

    # Adding inventory
    add_inventory(df_expenses,df_inventory)

    # Generate the income statement
    result = income_statement(df_income, 2024)
    print(f"Total Revenue: {result['total_revenue']}, Total COGS: {result['cogs']}, Operational Expense: {result['total_operational_expenses']}, Net Income: {result['net_profit']}")

if __name__ == "__main__":
    main()

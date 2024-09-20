import pandas as pd


# Read all CSV files and create DataFrames
df_income = pd.read_csv('data/Income.csv')
df_expenses = pd.read_csv('data/Expenses.csv')
df_liabilities = pd.read_csv('data/Liabilities.csv')

# Display the first few rows of each to ensure the data is loaded
print("Income Data:\n", df_income.head())
print("Expenses Data:\n", df_expenses.head())
print("Liabilities Data:\n", df_liabilities.head())

df_inventory = pd.DataFrame(columns=['sku','batch','quantity','unit_price','total_transaction','ean','asin','supplier'])

def add_inventory(expenses_df):
    for index, row in expenses_df.iterrows():
        if row['expense_type'] == 'purchase_inventory':
            inventory_row = {
                'sku': row['sku'],
                'batch': row['batch'],
                'quantity': row['quantity'],
                'unit_price': row['unit_price'],
                'total_transaction': row['total_transaction'],
                'ean': row['ean'],
                'asin': row['asin'],
                'supplier': row['channel']
            }
            
            df_inventory.loc[len(df_inventory)] = inventory_row

add_inventory(df_expenses)

print(df_inventory)


import pandas as pd


# Read all CSV files and create DataFrames
df_income = pd.read_csv('data/Income.csv')
df_expenses = pd.read_csv('data/Expenses.csv')
df_liabilities = pd.read_csv('data/Liabilities.csv')

# # Display the first few rows of each to ensure the data is loaded
# print("Income Data:\n", df_income.head())
# print("Expenses Data:\n", df_expenses.head())
# print("Liabilities Data:\n", df_liabilities.head())

df_inventory = pd.DataFrame(columns=['sku','batch','quantity','unit_price','total_transaction','ean','asin','supplier','total_cogs'])

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
            print('Total quantity', total_quantity_batch) 
            print('Initial unit price', row['unit_price'])

            # Total additional costs for this batch
            total_additional_costs = batch_shipping + batch_import_duties
            print('TOTAL ADDIONAL COST', total_additional_costs)

            # Calculate total COGS per BATCH and divide it to each item to get unit_price
            unit_price = row['unit_price'] + total_additional_costs / total_quantity_batch

            print('unit price',unit_price)
            print('batch import',batch_import_duties)
            print('batch ship',batch_shipping)

            inventory_row = {
                'sku': row['sku'],
                'batch': row['batch'],
                'quantity': row['quantity'],
                'unit_price': row['unit_price'],
                'total_transaction': row['total_transaction'],
                'ean': row['ean'],
                'asin': row['asin'],
                'supplier': row['channel'],
                'total_cogs': unit_price
            }
            
            df_inventory.loc[len(df_inventory)] = inventory_row

add_inventory(df_expenses)

print(df_inventory)

# prueba = df_inventory[df_inventory['sku'] == 162593].sort_values(by='batch')
# print(prueba)

# def calculate_cogs(sku, quantity_sold):
#     global df_inventory
#     cogs = 0
#     remaining_quantity = quantity_sold

#     # Filter inventory by SKU and sort by batch (FIFO)
#     sku_inventory_sorted = df_inventory[df_inventory['sku'] == sku].sort_values(by='batch')

#     for index, row in sku_inventory_sorted.iterrows():
#         if remaining_quantity == 0:
#             break

#         available_quantity = row['quantity']

#         if available_quantity <= quantity_sold:

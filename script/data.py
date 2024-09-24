# data.py

import pandas as pd
from utils import convert_date

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

# List of types of Other Incomes
other_income = [
    'Amazon Repayment',
    'Amazon Repayment for faulty Item'
]

# List of types of Operational Expenses
operational_expenses = [
    'Administrative Expense',
    'FBA storage fee',
    'Inbound Transportation Charge',
    'FBA Return Fee'
]

# Formatting colum DATE into a DateTime object
df_income = convert_date(df_income)
df_expenses = convert_date(df_expenses)
df_liabilities = convert_date(df_liabilities)
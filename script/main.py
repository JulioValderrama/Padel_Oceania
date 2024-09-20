import pandas as pd


# Read all CSV files and create DataFrames
df_income = pd.read_csv('data/Income.csv')
df_expenses = pd.read_csv('data/Expenses.csv')
df_liabilities = pd.read_csv('data/Liabilities.csv')

# Display the first few rows of each to ensure the data is loaded
print("Income Data:\n", df_income.head())
print("Expenses Data:\n", df_expenses.head())
print("Liabilities Data:\n", df_liabilities.head())
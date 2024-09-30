import matplotlib.pyplot as plt
import numpy as np
from fpdf import FPDF

# Function to calculate the percentage change (VAR%)
def calculate_var_percentage(current, previous):
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100

# Function to format numbers with two decimals
def format_value(value):
    return f'{float(value):,.2f}'  # Ensure we restrict to 2 decimal places

# Function to create a comparative table using matplotlib
def create_comparative_table(current_period, previous_period, current_period_label, previous_period_label):
    # Define the fields you want to compare
    fields = ['total_revenue', 'cogs', 'gross_margin', 'gross_margin_%', 'other_income', 'total_operational_expenses', 'operational_margin', 'taxes', 'net_profit', 'net_profit_%']
    row_labels = ['Total Revenue', 'COGS', 'Gross Margin', 'Gross Margin %', 'Other Income', 'Operational Expenses', 'Operational Margin', 'Taxes', 'Net Profit', 'Net Profit %']

    # Extract and format values from the dictionaries
    current_values = [format_value(current_period[field]) for field in fields]
    previous_values = [format_value(previous_period[field]) for field in fields]
    var_percentage = [format_value(calculate_var_percentage(current_period[field], previous_period[field])) for field in fields]

    # Create the table data
    table_data = np.array([previous_values, current_values, var_percentage]).T

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(8, 5))  # Set the figure size for better readability
    ax.axis('tight')
    ax.axis('off')

    # Create the table
    table = ax.table(cellText=table_data,
                     colLabels=[ f'Previous Period: {previous_period_label}', f'Current Period: {current_period_label}' ,'VAR %'],
                     rowLabels=row_labels,
                     loc='center',
                     cellLoc='center',  # Center-align text in the cells
                     colColours=['#D3D3D3'] * 3)  # Light grey for column headers

    # Set font size and apply alternating row colors
    table.auto_set_font_size(False)
    table.set_fontsize(10)

    # Set alternating row colors and bold key metrics
    green_rows = ['Gross Margin %', 'Operational Margin', 'Net Profit %']
    for i, row_label in enumerate(row_labels):
        if i % 2 == 0:
            row_color = '#F5F5F5'  # Light grey for alternating rows
        else:
            row_color = '#FFFFFF'  # White background for other rows

        # Apply green background for important rows
        if row_label in green_rows:
            row_color = '#90EE90'  # Light green background for key metrics

        # Apply the background color to the row
        for col in range(3):  # Apply to all 3 columns (current, previous, VAR %)
            table[(i + 1, col)].set_facecolor(row_color)

        # Bold font for key metrics
        if row_label in green_rows:
            for col in range(3):
                table[(i + 1, col)].set_text_props(weight='bold')

    # Adjust column width for better readability
    table.auto_set_column_width([0, 1, 2])

    # Show the table
    #plt.show()

# Function to export the comparative table to a PDF file using fpdf
def export_to_pdf(current_period, previous_period, current_period_label, previous_period_label):
    pdf = FPDF()
    pdf.add_page()

    # Title section
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(0, 102, 204)  # Blue title text
    pdf.cell(200, 15, "Profit and Loss Statement", ln=True, align='C')
    pdf.ln(10)

    # Period information with custom background
    pdf.set_fill_color(240, 240, 240)  # Light grey background for headers
    pdf.set_text_color(0)  # Reset text color to black
    pdf.set_font("Arial", 'B', 12)
    
    pdf.cell(60, 10, 'Item', 1, fill=True, align='C')
    pdf.cell(50, 10, f'Period: {previous_period_label}', 1, fill=True, align='C')
    pdf.cell(50, 10, f'Period: {current_period_label}', 1, fill=True, align='C')
    pdf.cell(30, 10, 'VAR %', 1, fill=True, align='C')
    pdf.ln()

    # Set up the green background for specific rows
    green_rows = ['Gross Margin %', 'Operational Margin', 'Net Profit %']

    # Define the fields you want to compare
    fields = ['total_revenue', 'cogs', 'gross_margin', 'gross_margin_%', 'other_income', 'total_operational_expenses', 'operational_margin', 'taxes', 'net_profit', 'net_profit_%']
    row_labels = ['Total Revenue', 'COGS', 'Gross Margin', 'Gross Margin %', 'Other Income', 'Operational Expenses', 'Operational Margin', 'Taxes', 'Net Profit', 'Net Profit %']

    # Alternating row background color
    row_bg_color = [255, 255, 255]  # Default white
    alternate_bg_color = [245, 245, 245]  # Light grey

    # Loop through fields and print them
    for i, field in enumerate(fields):
        current_value = current_period[field]
        previous_value = previous_period[field]
        var_value = calculate_var_percentage(current_value, previous_value)

        # Format values for printing (restrict to 2 decimal places)
        current_value_str = format_value(current_value)
        previous_value_str = format_value(previous_value)
        var_value_str = format_value(var_value)

        # Alternate row colors
        fill_color = alternate_bg_color if i % 2 == 1 else row_bg_color
        pdf.set_fill_color(*fill_color)

        # Check if the row needs a green background (highlight important rows)
        if row_labels[i] in green_rows:
            pdf.set_font("Arial", 'B', 12)
            pdf.set_fill_color(144, 238, 144)  # Green background (light green)
            fill = True
        else:
            pdf.set_font("Arial", '', 12)
            fill = False

        # Print row label, values, and VAR %
        pdf.cell(60, 10, row_labels[i], 1, fill=True)
        pdf.cell(50, 10, previous_value_str, 1, fill=True)
        pdf.cell(50, 10, current_value_str, 1, fill=True)
        pdf.cell(30, 10, var_value_str, 1, fill=True)
        pdf.ln()

    # Output the PDF to a file
    pdf.output("Income_Statement_Report_Enhanced.pdf")

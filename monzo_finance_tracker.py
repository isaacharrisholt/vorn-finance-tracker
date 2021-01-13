# Imports...
import json
import sys
from datetime import datetime

import pandas as pd

from lib import parser
from lib import spreadsheet_manager as sm

# Checks to see if user has passed transaction data CSV file path as argument. If not, user manually inputs file path
try:
    csv_path = sys.argv[1]
except IndexError:
    csv_path = input("\nPlease input the transaction data file path. Transaction data should be in a CSV file "
                     "downloaded from the Monzo app:\n")

# Validates that file path is a path to a proper CSV file by attempting to read file with pandas
# User must keep inputting file path until valid
while True:
    try:
        transaction_data = pd.read_csv(csv_path).fillna("")
    except (KeyError, FileNotFoundError):
        csv_path = input("\nThat's not a valid CSV file. Please input the transaction data file path. Transaction "
                         "data should be in a CSV file downloaded from the Monzo app:\n")
        continue
    break

# Next two try/except blocks do the same as above but for the XLSX file
try:
    xlsx_path = sys.argv[2]
except IndexError:
    xlsx_path = input("\nPlease input the file path for the spreadsheet XLSX file:\n")

while True:
    # Uses spreadsheet_manager function to avoid importing openpyxl here
    if not sm.validate_spreadsheet(xlsx_path):
        xlsx_path = input("\nThat's not a valid XLSX file. Please input the file path for the spreadsheet XLSX file:\n")
        continue
    break

# Validates that CSV file given is a valid Monzo transaction data CSV by checking column headings, else exits program
try:
    months = [int(datetime.strptime(date, "%d/%m/%Y").month) for date in transaction_data["Date"]]
    vendors = [vendor.lower() for vendor in transaction_data["Name"]]
    amounts = [round(amount, 2) for amount in transaction_data["Amount"]]
    references = [reference for reference in transaction_data["Notes and #tags"]]
    transaction_ids = [tid for tid in transaction_data["Transaction ID"]]
except KeyError:
    print("\nThis may not be a valid Monzo transaction data file. Please try again, and if the issue persists, contact "
          "the developer.")
    exit()

# Generates dictionaries of user income and outgoings categories and rows of the spreadsheet
with open("./files/outgoings_categories.txt", "r") as out_cats, open("./files/income_categories.txt", "r") as in_cats:
    outgoings_categories = {}
    income_categories = {}

    for line in out_cats.read().splitlines():
        category_and_row = line.strip().split(":")
        user_category = category_and_row[0].strip().lower()
        row = category_and_row[1].replace(" ", "-")

        outgoings_categories[user_category] = row

    for line in in_cats.read().splitlines():
        category_and_row = line.strip().split(":")
        user_category = category_and_row[0].strip().lower()
        row = category_and_row[1].replace(" ", "-")

        income_categories[user_category] = row

    out_cats.close()
    in_cats.close()

# Creates dictionaries based on months that transactions occurred, and creates sub-dictionaries to store categorised
# transaction balances
outgoings_balances = {month: {cat: 0 for cat in outgoings_categories} for month in months}
income_balances = {month: {cat: 0 for cat in income_categories} for month in months}

# Two variables to store total amount spent and received across all transactions
total_in = 0
total_out = 0

# Loads transaction history (a list of previously processed transaction IDs)
with open("files/transaction_history.json", "r") as transaction_history_file:
    transaction_history = json.load(transaction_history_file)
    transaction_history_file.close()

# Iterates through transactions. Uses height of transaction_data DataFrame as number of iterations
for i in range(0, transaction_data.shape[0]):
    transaction_id = transaction_ids[i]

    # Checks that current transaction has not already been processed to avoid incorrect output to final spreadsheet
    if transaction_id in transaction_history:
        print("\nTransaction processed previously, skipping...")
        continue

    # Assigns transaction data to individual variables for ease of access/improved readability
    month = months[i]
    vendor = vendors[i]
    amount = amounts[i]
    reference = references[i]

    # Categorises transaction as income or outgoing and ignores transactions of £0.00 (such as card checks)
    if amount > 0:
        # Uses parser to get category
        category = parser.parse_category("income", month, vendor, amount, reference, income_categories)
        # Stores amount
        income_balances[month][category] += abs(amount)
        total_in += abs(amount)
    elif amount < 0:
        # Same as above but for outgoings
        category = parser.parse_category("outgoings", month, vendor, amount, reference, outgoings_categories)
        outgoings_balances[month][category] += abs(amount)
        total_out += abs(amount)

    # If transaction was processed successfully, stores it in transaction history
    transaction_history.append(transaction_id)

# Rounds data to 2 decimal places because... Python
for month in outgoings_balances:
    for key in outgoings_balances[month]:
        outgoings_balances[month][key] = round(outgoings_balances[month][key], 2)

for month in income_balances:
    for key in income_balances[month]:
        income_balances[month][key] = round(income_balances[month][key], 2)

# Inserts data into spreadsheet
sm.insert_into_spreadsheet(xlsx_path, outgoings_categories, income_categories, outgoings_balances, income_balances)

# Saves transaction history
with open("files/transaction_history.json", "w") as transaction_history_file:
    json.dump(transaction_history, transaction_history_file)
    transaction_history_file.close()

# Final statement to user
print(f"\n\nDone!\nTotal money in: £{round(total_in, 2)}\nTotal money out: £{round(total_out, 2)}\nNet change: "
      f"£{round(total_in - total_out, 2)}\n\n")

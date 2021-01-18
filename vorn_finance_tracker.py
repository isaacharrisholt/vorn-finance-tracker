# Imports...
import json
import sys
from datetime import datetime

import pandas as pd

from lib import parser
from lib import spreadsheet_manager as sm
from lib.utils import cls

cls()

# Checks to see if user has passed transaction data CSV file path as argument. If not, user manually inputs file path
try:
    csv_path = sys.argv[1]
except IndexError:
    csv_path = input("\nPlease input the transaction data file path. Transaction data should be in a CSV file "
                     "downloaded from your bank:\n")
    cls()

# Validates that file path is a path to a proper CSV file by attempting to read file with pandas
# User must keep inputting file path until valid
while True:
    try:
        transaction_data = pd.read_csv(csv_path).fillna("")
    except (KeyError, FileNotFoundError):
        csv_path = input("\nThat's not a valid CSV file. Please input the transaction data file path. Transaction "
                         "data should be in a CSV file downloaded from your bank:\n")
        cls()
        continue
    break

# Next two try/except blocks do the same as above but for the XLSX file
try:
    xlsx_path = sys.argv[2]
except IndexError:
    xlsx_path = input("\nPlease input the file path for the spreadsheet XLSX file:\n")
    cls()

while True:
    # Uses spreadsheet_manager function to avoid importing openpyxl here
    if not sm.validate_spreadsheet(xlsx_path):
        xlsx_path = input("\nThat's not a valid XLSX file. Please input the file path for the spreadsheet XLSX file:\n")
        cls()
        continue
    break

with open("files/user_and_bank_data.json", "r") as user_and_bank_data_file:
    user_and_bank_data = json.load(user_and_bank_data_file)
    user_and_bank_data_file.close()

valid_banks = [bank for bank in user_and_bank_data["banks"]]

if user_and_bank_data["user"]["bank"] == "":
    while True:
        user_bank = input(f"\nWhich of the following banks do you bank with? Options "
                          f"are: {', '.join([bank.replace('-', ' ').title() for bank in valid_banks])}\nOr type "
                          f"\"Other\" if you bank with a different bank.\n").lower().strip().replace(" ", "-")
        cls()

        if user_bank in valid_banks:
            user_and_bank_data["user"]["bank"] = user_bank
        elif user_bank == "other":
            user_and_bank_data = parser.parse_bank(user_and_bank_data, transaction_data)
            user_bank = user_and_bank_data["user"]["bank"]
        else:
            print("\nInvalid selection, try again.")
            continue

        with open("files/user_and_bank_data.json", "w") as user_and_bank_data_file:
            json.dump(user_and_bank_data, user_and_bank_data_file, indent=4)
            user_and_bank_data_file.close()

        break
else:
    user_bank = user_and_bank_data["user"]["bank"]

if user_and_bank_data["user"]["currency"] == "":

    currency_symbol = input(f"\nWhat currency symbol should the program use?\n").lower().strip().replace(" ", "-")
    cls()

    user_and_bank_data["user"]["currency"] = currency_symbol

    with open("files/user_and_bank_data.json", "w") as user_and_bank_data_file:
        json.dump(user_and_bank_data, user_and_bank_data_file, indent=4)
        user_and_bank_data_file.close()

else:
    currency_symbol = user_and_bank_data["user"]["currency"]

date_key = user_and_bank_data["banks"][user_bank]["date"]
vendor_key = user_and_bank_data["banks"][user_bank]["vendor"]
amount_key = user_and_bank_data["banks"][user_bank]["amount"]
reference_key = user_and_bank_data["banks"][user_bank]["reference"]
transaction_id_key = user_and_bank_data["banks"][user_bank]["transaction_id"]

date_format = user_and_bank_data["banks"][user_bank]["date_format"]

months = [int(datetime.strptime(date, date_format).month) for date in transaction_data[date_key]]
vendors = [vendor.lower() for vendor in transaction_data[vendor_key]]
amounts = [round(amount, 2) for amount in transaction_data[amount_key]]
references = [reference for reference in transaction_data[reference_key]]

if transaction_id_key != "":
    transaction_ids = [tid for tid in transaction_data[transaction_id_key]]
    use_transaction_id = True
else:
    use_transaction_id = False

# Generates dictionaries of user income and outgoings categories and rows of the spreadsheet
with open("./files/outgoings_categories.txt", "r") as out_cats, open("./files/income_categories.txt", "r") as in_cats:
    outgoings_categories = {}
    income_categories = {}

    for line in out_cats.read().splitlines():
        category_and_row = line.strip().split(":")
        user_category = category_and_row[0].strip().lower()
        row = category_and_row[1].replace(" ", "")

        outgoings_categories[user_category] = row

    for line in in_cats.read().splitlines():
        category_and_row = line.strip().split(":")
        user_category = category_and_row[0].strip().lower()
        row = category_and_row[1].replace(" ", "")

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
    if use_transaction_id:
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

    # Categorises transaction as income or outgoing and ignores transactions of 0.00 (such as card checks)
    if amount > 0:
        # Uses parser to get category
        category = parser.parse_category("income", month, vendor, amount, reference, income_categories, currency_symbol)
        # Stores amount
        income_balances[month][category] += abs(amount)
        total_in += abs(amount)
    elif amount < 0:
        # Same as above but for outgoings
        category = parser.parse_category("outgoings", month, vendor, amount, reference, outgoings_categories,
                                         currency_symbol)
        outgoings_balances[month][category] += abs(amount)
        total_out += abs(amount)

    if use_transaction_id:
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

if use_transaction_id:
    # Saves transaction history
    with open("files/transaction_history.json", "w") as transaction_history_file:
        json.dump(transaction_history, transaction_history_file, indent=4)
        transaction_history_file.close()

# Final statement to user
print(f"\n\nDone!\nTotal money in: {currency_symbol}{round(total_in, 2)}\nTotal money out: "
      f"{currency_symbol}{round(total_out, 2)}\nNet change: {currency_symbol}{round(total_in - total_out, 2)}\n\n")

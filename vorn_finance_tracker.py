# Imports...
import json
import sys

import pandas as pd

from lib import parser
from lib import spreadsheet_manager as sm
from lib.utils import cls, pprint, pinput

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
        csv_path = pinput("\n{RED}That's not a valid CSV file.{RESET} Please input the transaction data file path. "
                          "Transaction data should be in a CSV file downloaded from your bank:\n")
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
        xlsx_path = pinput("\n{RED}That's not a valid XLSX file.{RESET} Please input the file path for the spreadsheet "
                           "XLSX file:\n")
        cls()
        continue
    break

# Gets user and bank data from file
with open("files/user_and_bank_data.json", "r") as user_and_bank_data_file:
    user_and_bank_data = json.load(user_and_bank_data_file)
    user_and_bank_data_file.close()

# Creates a list of valid banks for user to choose from
valid_banks = [bank for bank in user_and_bank_data["banks"]]

if user_and_bank_data["user"]["bank"] == "":
    while True:
        user_bank = pinput(f"\nWhich of the following banks do you bank with? Options "
                          f"are: {', '.join([bank.replace('-', ' ').title() for bank in valid_banks])}\nOr type "
                          f"\"Other\" if you bank with a different bank.\n").lower().strip().replace(" ", "-")
        cls()

        # Validates user input
        if user_bank in valid_banks:
            user_and_bank_data["user"]["bank"] = user_bank
        elif user_bank == "other":
            # If user wants to set up a new bank, starts process
            user_and_bank_data = parser.parse_bank(user_and_bank_data, transaction_data)
            user_bank = user_and_bank_data["user"]["bank"]
        else:
            pprint("\n{RED}Invalid selection, try again.{RESET}")
            continue

        # Saves data and closes file
        with open("files/user_and_bank_data.json", "w") as user_and_bank_data_file:
            json.dump(user_and_bank_data, user_and_bank_data_file, indent=4)
            user_and_bank_data_file.close()

        break
else:
    user_bank = user_and_bank_data["user"]["bank"]

# Checks if user already has a currency symbol set as default. If not, user chooses one.
if user_and_bank_data["user"]["currency"] == "":
    currency_symbol = input(f"\nWhat currency symbol should the program use?\n").lower().strip().replace(" ", "-")
    cls()

    user_and_bank_data["user"]["currency"] = currency_symbol

    with open("files/user_and_bank_data.json", "w") as user_and_bank_data_file:
        json.dump(user_and_bank_data, user_and_bank_data_file, indent=4)
        user_and_bank_data_file.close()

else:
    currency_symbol = user_and_bank_data["user"]["currency"]

# Gets keys from the user and bank data for the transaction data headings
date_key = user_and_bank_data["banks"][user_bank]["date"]
vendor_key = user_and_bank_data["banks"][user_bank]["vendor"]
amount_key = user_and_bank_data["banks"][user_bank]["amount"]
reference_key = user_and_bank_data["banks"][user_bank]["reference"]
transaction_id_key = user_and_bank_data["banks"][user_bank]["transaction_id"]
date_format = user_and_bank_data["banks"][user_bank]["date_format"]

# Stores a bool of whether the bank CSV contains transaction IDs
use_transaction_id = transaction_id_key != ""

# Creates a new DataFrame with only relevant information with new, known headings
transaction_df = pd.DataFrame(index=transaction_data.index)
transaction_df["Months"] = pd.to_datetime(transaction_data[date_key], format=date_format).dt.month
transaction_df["Vendors"] = transaction_data[vendor_key].str.lower()
transaction_df["Amounts"] = transaction_data[amount_key].round(2)
transaction_df["References"] = transaction_data[reference_key]
transaction_df["Categories"] = ""

if use_transaction_id:
    transaction_df["Transaction IDs"] = transaction_data[transaction_id_key]
else:
    transaction_df["Transaction IDs"] = ""

# Deletes old DataFrame as it's no longer needed, and may be quite large
del transaction_data

# Generates a dictionary of user transaction categories and rows of the spreadsheet
with open("./files/outgoings_categories.txt", "r") as out_cats, open("./files/income_categories.txt", "r") as in_cats:
    categories = {"income": {}, "outgoings": {}}

    for line in out_cats.read().splitlines():
        category_and_row = line.strip().split(":")
        user_category = category_and_row[0].strip().lower()
        row = category_and_row[1].replace(" ", "")

        categories["outgoings"][user_category] = row

    for line in in_cats.read().splitlines():
        category_and_row = line.strip().split(":")
        user_category = category_and_row[0].strip().lower()
        row = category_and_row[1].replace(" ", "")

        categories["income"][user_category] = row

    out_cats.close()
    in_cats.close()

# Loads transaction history (a list of previously processed transaction IDs)
with open("files/transaction_history.json", "r") as transaction_history_file:
    transaction_history = json.load(transaction_history_file)
    transaction_history_file.close()

# Creates a copy of transaction history that won't be edited for totalling later in the program
transaction_history_for_totals = transaction_history.copy()

# Iterates through transactions. Uses height of transaction_data DataFrame as number of iterations
for i in range(0, transaction_df.shape[0]):

    # Creates copy slice of main DataFrame to pass to parser
    transaction = transaction_df.iloc[i].copy()

    # Checks if transaction IDs are being used
    if use_transaction_id:
        transaction_id = transaction["Transaction IDs"]

        # Checks that current transaction has not already been processed to avoid incorrect output to final spreadsheet
        if transaction_id in transaction_history:
            pprint("\n{BLUE}Transaction processed previously, skipping...{RESET}")
            continue

    # Uses parser to get category
    category = parser.parse_category(transaction, categories, currency_symbol)
    # Update main DataFrame
    transaction_df.loc[i, "Categories"] = category

    if use_transaction_id:
        # If transaction was processed successfully, stores it in transaction history
        transaction_history.append(transaction_id)


# Two variables to store total amount spent and received across all transactions
can_use = ~transaction_df["Transaction IDs"].isin(transaction_history_for_totals)
total_in = round(transaction_df.where(can_use).loc[transaction_df["Amounts"] > 0, "Amounts"].sum(), 2)
total_out = round(abs(transaction_df.where(can_use).loc[transaction_df["Amounts"] < 0, "Amounts"].sum()), 2)


# Inserts data into spreadsheet
sm.insert_into_spreadsheet(xlsx_path, categories, transaction_df)

if use_transaction_id:
    # Saves transaction history
    with open("files/transaction_history.json", "w") as transaction_history_file:
        json.dump(transaction_history, transaction_history_file, indent=4)
        transaction_history_file.close()

# Final statement to user
pprint(f"\n\nDone!\nTotal money in: {{GREEN}}{currency_symbol}{total_in}{{RESET}}\nTotal money out: "
       f"{{RED}}{currency_symbol}{total_out}\n{{RESET}}Net change: {{BLUE}}{currency_symbol}{total_in - total_out}"
       f"{{RESET}}\n\n")

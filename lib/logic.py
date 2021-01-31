# Imports once again...
import json
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import pandas as pd

from . import spreadsheet_manager as sm
from .utils import cls, pprint, pinput


def get_transaction_data(argv):
    # Create a Tk object to hide root window when using file dialog
    root = Tk()
    root.withdraw()
    # Checks to see if user has passed transaction data CSV file path as argument. If not, user manually inputs file
    # path
    try:
        csv_path = argv[1]
    except IndexError:
        pinput("Press {YELLOW}Enter{RESET} then browse to your transaction data file. Transaction data should be in a "
               "CSV file downloaded from your bank.")
        csv_path = askopenfilename(filetypes=[("CSV Files", "*.csv")]).replace("\\", "/")
        cls()

    # Validates that file path is a path to a proper CSV file by attempting to read file with pandas
    # User must keep inputting file path until valid
    while True:
        try:
            if csv_path[-4:] != ".csv":
                raise KeyError
            transaction_data = pd.read_csv(csv_path)
        except (KeyError, FileNotFoundError, pd.errors.ParserError):
            pprint("{RED}That's not a valid CSV file.{RESET} Try again and choose the transaction data file. "
                   "Transaction data should be in a CSV file downloaded from your bank.")
            csv_path = askopenfilename().replace("\\", "/")
            cls()
            continue
        break
    return transaction_data


def get_spreadsheet_path(argv):
    # Create a Tk object to hide root window when using file dialog
    root = Tk()
    root.withdraw()
    # Next two try/except blocks do the same as above but for the XLSX file
    try:
        xlsx_path = argv[2]
    except IndexError:
        pinput("Press {YELLOW}Enter{RESET} then browse to your spreadsheet file.")
        xlsx_path = askopenfilename().replace("\\", "/")
        cls()

    while True:
        # Uses spreadsheet_manager function to avoid importing openpyxl here
        if not sm.validate_spreadsheet(xlsx_path):
            pprint("{RED}Your input is not a valid XLSX file.{RESET} Try again and choose your spreadsheet file.")
            xlsx_path = askopenfilename().replace("\\", "/")
            cls()
            continue
        break
    return xlsx_path


def get_bank(user_and_bank_data, transaction_data):
    # Creates a list of valid banks for user to choose from
    valid_banks = [bank for bank in user_and_bank_data["banks"]]
    valid_banks_string = '{RESET}\n{YELLOW}'.join([bank.replace('-', ' ').title() for bank in valid_banks])

    while True:
        user_bank = pinput(f"Which of the following banks do you bank with? Options are:\n{{YELLOW}}"
                           f"{valid_banks_string}\n{{RESET}}Or type \"Other\" if you bank with a different bank or "
                           f"would like to overwrite the settings for an existing "
                           f"bank.").lower().strip().replace(" ", "-")
        cls()

        # Validates user input
        if user_bank in valid_banks:
            user_and_bank_data["user"]["bank"] = user_bank
        elif user_bank == "other":
            # If user wants to set up a new bank, starts process
            user_and_bank_data = setup_bank(user_and_bank_data, transaction_data)
            user_bank = user_and_bank_data["user"]["bank"]
        else:
            pprint("{RED}Invalid selection, try again.{RESET}")
            continue

        # Saves data and closes file
        with open("files/user_and_bank_data.json", "w") as user_and_bank_data_file:
            json.dump(user_and_bank_data, user_and_bank_data_file, indent=4)
            user_and_bank_data_file.close()

        break
    return user_bank


def get_currency(user_and_bank_data):
    currency_symbol = pinput("What currency symbol should the program use?").lower().strip().replace(" ", "-")
    cls()

    user_and_bank_data["user"]["currency"] = currency_symbol

    with open("files/user_and_bank_data.json", "w") as user_and_bank_data_file:
        json.dump(user_and_bank_data, user_and_bank_data_file, indent=4)
        user_and_bank_data_file.close()

    return currency_symbol


def create_transaction_df(user_and_bank_data, transaction_data):
    user_bank = user_and_bank_data["user"]["bank"]

    # Gets keys from the user and bank data for the transaction data headings
    date_key = user_and_bank_data["banks"][user_bank]["date"]
    vendor_key = user_and_bank_data["banks"][user_bank]["vendor"]
    reference_key = user_and_bank_data["banks"][user_bank]["reference"]

    # Parses amount data based on stored type
    amount_data_type = user_and_bank_data["banks"][user_bank]["amount"]["type"]

    if amount_data_type == 1:
        amount_key = user_and_bank_data["banks"][user_bank]["amount"]["header"]
        amounts_data = transaction_data[amount_key].round(2).fillna(0)
    elif amount_data_type == 2:
        income_key = user_and_bank_data["banks"][user_bank]["amount"]["income"]
        outgoings_key = user_and_bank_data["banks"][user_bank]["amount"]["outgoings"]
        income_data = transaction_data[income_key].abs()
        outgoings_data = transaction_data[outgoings_key].abs() * -1
        amounts_data = income_data.add(outgoings_data, fill_value=0).round(2)
    elif amount_data_type == 3:
        amount_key = user_and_bank_data["banks"][user_bank]["amount"]["header"]
        type_key = user_and_bank_data["banks"][user_bank]["amount"]["transaction_type"]
        outgoings_keyword = user_and_bank_data["banks"][user_bank]["amount"]["outgoings_keyword"]
        amounts_data = transaction_data[amount_key].abs().round(2).fillna(0)
        amounts_data[transaction_data[type_key] == outgoings_keyword] = amounts_data[transaction_data[type_key] ==
                                                                                     outgoings_keyword] * -1

    day_first = user_and_bank_data["banks"][user_bank]["day_first"]

    # Stores a bool of whether the bank CSV contains transaction IDs
    transaction_id_key = user_and_bank_data["banks"][user_bank]["transaction_id"]
    use_transaction_id = (transaction_id_key != "")

    # Creates a new DataFrame with only relevant information with new, known headings
    transaction_df = pd.DataFrame(index=transaction_data.index)
    transaction_df["Months"] = pd.to_datetime(transaction_data[date_key], dayfirst=day_first).dt.month
    transaction_df["Vendors"] = transaction_data[vendor_key].str.lower().fillna("")
    transaction_df["Amounts"] = amounts_data
    transaction_df["References"] = transaction_data[reference_key].fillna("None")
    transaction_df["Categories"] = ""

    if use_transaction_id:
        transaction_df["Transaction IDs"] = transaction_data[transaction_id_key]
    else:
        transaction_df["Transaction IDs"] = ""

    return transaction_df, use_transaction_id


def update_transaction_df(transaction_df, transaction_history, use_transaction_id, categories, currency_symbol):
    # Iterates through transactions. Uses height of transaction_data DataFrame as number of iterations
    for i in range(0, transaction_df.shape[0]):

        # Creates copy slice of main DataFrame to pass to parser
        transaction = transaction_df.iloc[i].copy()

        # Checks if transaction IDs are being used
        if use_transaction_id:
            transaction_id = transaction["Transaction IDs"]

            # Checks that current transaction has not already been processed to avoid incorrect output to final
            # spreadsheet
            if transaction_id in transaction_history:
                pprint("\n{YELLOW}Transaction processed previously, skipping...{RESET}")
                continue

        # Uses parser to get category
        category = parse_category(transaction, categories, currency_symbol)
        # Update main DataFrame
        transaction_df.loc[i, "Categories"] = category

        if use_transaction_id:
            # If transaction was processed successfully, stores it in transaction history
            transaction_history.append(transaction_id)

    return transaction_df, transaction_history


def get_categories():
    # Generates a dictionary of user transaction categories and rows of the spreadsheet
    with open("files/outgoings_categories.txt", "r") as out_cats, open("files/income_categories.txt",
                                                                       "r") as in_cats:
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
    return categories


# Function to parse the transaction category for an incoming transaction
def parse_category(transaction, categories, currency_symbol):
    # Assigns transaction data to individual variables for ease of access/improved readability
    month = transaction["Months"]
    vendor = transaction["Vendors"]
    amount = transaction["Amounts"]
    reference = transaction["References"]

    # Categorises transaction as income or outgoings
    if amount > 0:
        transaction_type = "income"
    elif amount < 0:
        transaction_type = "outgoings"
    else:
        return ""

    # Gets category options for the transaction type
    category_options = categories[transaction_type]

    # Retrieve the category map
    category_map = get_category_map(transaction_type)

    # If we already have the category stored return it
    if vendor in category_map:
        return category_map[vendor]
    else:
        # Create a string of categories to display to the user
        categories = "{RESET}, {YELLOW}".join(category_options)

        # Display transaction info to user and have user classify the transaction. If user input is not valid, ask again
        while True:
            if transaction_type == "income":
                category = pinput(
                    f"What category does the following {{GREEN}}{transaction_type}{{RESET}} transaction come under?\n\n"
                    f"Month: {{YELLOW}}{month}{{RESET}}\n"
                    f"Amount: {{GREEN}}{currency_symbol}{amount}{{RESET}}\n"
                    f"Vendor: {{YELLOW}}{vendor.title()}{{RESET}}\n"
                    f"Reference: {{YELLOW}}{reference}{{RESET}}\n\n"
                    f"Category options are: {{YELLOW}}{categories}{{RESET}}\n"
                    f"Alternatively type {{YELLOW}}ignore{{RESET}} to ignore this transaction.").lower().strip()
            else:
                category = pinput(
                    f"What category does the following {{RED}}{transaction_type}{{RESET}} transaction come under?\n\n"
                    f"Month: {{YELLOW}}{month}{{RESET}}\n"
                    f"Amount: {{RED}}{currency_symbol}{amount}{{RESET}}\n"
                    f"Vendor: {{YELLOW}}{vendor.title()}{{RESET}}\n"
                    f"Reference: {{YELLOW}}{reference}{{RESET}}\n\n"
                    f"Category options are: {{YELLOW}}{categories}{{RESET}}\n"
                    f"Alternatively type {{YELLOW}}ignore{{RESET}} to ignore this transaction.").lower().strip()

            if category == "ignore":
                cls()
                return ""
            elif category not in category_options:
                pprint("{RED}Invalid category.{RESET}")
                continue
            else:
                break

        # Ask if user wants to save the category as default for categories of this type with this vendor if vendor is
        # not blank
        if vendor != "":
            while True:
                user_input = pinput(
                    f"Would you like to save {{YELLOW}}{category}{{RESET}} as the category for {{YELLOW}}"
                    f"{transaction_type}{{RESET}} transactions with {{YELLOW}}{vendor.title()}{{RESET}}? "
                    f"[{{GREEN}}Y{{RESET}}/{{RED}}N{{RESET}}]").lower().strip()
                cls()

                try:
                    if user_input[0] not in ["y", "n"]:
                        raise IndexError
                    else:
                        break
                except IndexError:
                    pprint("{RED}Invalid input.{RESET}")
                    continue

            # If user wants category saved, dave it and update the category mapping file
            if user_input[0] == "y":
                category_map[vendor] = category
                update_category_map(transaction_type, category_map)
                pprint("{GREEN}Category saved.{RESET}")
            else:
                pprint("{RED}Category not saved.{RESET}")

        # Return transaction category
        return category


# If user doesn't bank with bank already saved, get CSV headings from user for new bank, then return it
def setup_bank(user_and_bank_data, transaction_data):
    # Gets name of user's bank and confirms it
    while True:
        user_bank = pinput("What is the name of your bank?").strip()

        while True:
            user_input = pinput(f"Your bank is {{YELLOW}}{user_bank}{{RESET}}, is that correct? "
                                f"[{{GREEN}}Y{{RESET}}/{{RED}}N{{RESET}}]").lower().strip()
            cls()

            try:
                if user_input[0] not in ["y", "n"]:
                    raise IndexError
                else:
                    break
            except IndexError:
                pprint("{RED}Invalid input.{RESET}")
                continue

        if user_input[0] == "y":
            break

    # Formats and saves user's bank name
    user_bank_lowered = user_bank.lower().replace(" ", "-")
    user_and_bank_data["user"]["bank"] = user_bank_lowered
    user_and_bank_data["banks"][user_bank_lowered] = {}
    user_and_bank_data["banks"][user_bank_lowered]["amount"] = {}

    # Provides user with information on the process that is about to occur
    pinput("You will now be asked to identify the header titles corresponding to certain pieces of information in "
           "your CSV of transaction data from your bank. Your answers are case sensitive, so please take care when "
           "typing. Press {YELLOW}Enter{RESET} to continue.")

    required_info = ["date", "vendor", "reference"]

    # Gets user to input CSV headers for all required information
    for info in required_info:
        while True:
            csv_header = pinput(f"What is the header for the {{YELLOW}}{info}{{RESET}} information in your CSV "
                                f"file?").strip()
            cls()

            try:
                transaction_data[csv_header]
            except KeyError:
                pprint("{RED}That doesn't seem to be a valid header, please try again.{RESET}")
                continue
            break

        user_and_bank_data["banks"][user_bank_lowered][info] = csv_header

        if info == "date":
            while True:
                day_first = pinput("Does your CSV file store dates with day first or month first? Type {YELLOW}day"
                                   "{RESET} or {YELLOW}month{RESET} to select.").strip().lower()

                if day_first not in ["day", "month"]:
                    pprint("{RED}Invalid input.{RESET}")
                    continue

                if day_first == "day":
                    user_and_bank_data["banks"][user_bank_lowered]["day_first"] = True
                else:
                    user_and_bank_data["banks"][user_bank_lowered]["day_first"] = False

                cls()
                break

    # Determines structure of CSV in terms of how transaction amounts are stored
    while True:
        data_type = pinput("How is transaction amount data stored in your CSV file? Options are:\n"
                           "1. A single column with positive and negative numbers\n"
                           "2. Two columns: one with incoming transactions, and one with outgoing transactions\n"
                           "3. Two columns: one with the transaction amount, and one with transaction type (e.g."
                           " \"{YELLOW}income{RESET}\"/\"{YELLOW}outgoing{RESET}\")").strip()
        cls()

        try:
            data_type = int(data_type)
            if data_type not in range(1, 4):
                raise ValueError
        except ValueError:
            pprint("{RED}Invalid input.{RESET}")
            continue
        user_and_bank_data["banks"][user_bank_lowered]["amount"]["type"] = data_type
        break

    if data_type == 1:
        while True:
            amount_header = pinput("What is the header for the {YELLOW}amount{RESET} information in your CSV "
                                   "file?").strip()
            cls()

            try:
                transaction_data[amount_header]
            except KeyError:
                pprint("{RED}That doesn't seem to be a valid header, please try again.{RESET}")
                continue
            break
        user_and_bank_data["banks"][user_bank_lowered]["amount"]["header"] = amount_header
    elif data_type == 2 or data_type == 3:
        if data_type == 2:
            required_headers = ["income", "outgoings"]
        else:
            required_headers = ["header", "transaction_type"]

        for header in required_headers:
            while True:
                amount_header = pinput(f"What is the header for the {{YELLOW}}"
                                       f"{header.replace('_', ' ').replace('header', 'amount')}"
                                       f"{{RESET}} information in your CSV file?").strip()
                cls()

                try:
                    transaction_data[amount_header]
                except KeyError:
                    pprint("{RED}That doesn't seem to be a valid header, please try again.{RESET}")
                    continue
                break
            user_and_bank_data["banks"][user_bank_lowered]["amount"][header] = amount_header

        if data_type == 3:
            required_type_keywords = ["income", "outgoings"]
            for requirement in required_type_keywords:
                keyword = pinput(f"What is the keyword for the {{YELLOW}}{requirement}{{RESET}} transaction type in "
                                 f"this column?").strip().lower()
                cls()
                user_and_bank_data["banks"][user_bank_lowered]["amount"][requirement + "_keyword"] = keyword

    # Determines if CSV contains transaction IDs, and if so, asks user to input CSV header
    while True:
        user_input = pinput("Does your CSV file contain transaction IDs issued by your bank? "
                            "[{GREEN}Y{RESET}/{RED}N{RESET}]").lower().strip()
        cls()

        try:
            if user_input[0] not in ["y", "n"]:
                raise IndexError
            else:
                break
        except IndexError:
            pprint("{RED}Invalid input.{RESET}")
            continue

    if user_input[0] == "y":
        while True:
            csv_header = pinput(f"What is the header for the transaction ID information in your CSV file?").strip()
            cls()

            try:
                transaction_data[csv_header]
            except KeyError:
                pprint("{RED}That doesn't seem to be a valid header, please try again.{RESET}")
                continue
            break

        user_and_bank_data["banks"][user_bank_lowered]["transaction_id"] = csv_header
    else:
        # Else leaves transaction ID header blank in file
        user_and_bank_data["banks"][user_bank_lowered]["transaction_id"] = ""

    return user_and_bank_data


# Function to get the category map as a dictionary for a given transaction type
def get_category_map(transaction_type):
    with open(f"files/mappings/{transaction_type}_mapping.json", "r") as f:
        category_map = json.load(f)
        f.close()
    return category_map


# Function to update the category map file of a given transaction type
def update_category_map(transaction_type, category_map):
    with open(f"files/mappings/{transaction_type}_mapping.json", "w") as f:
        json.dump(category_map, f, indent=4)
        f.close()

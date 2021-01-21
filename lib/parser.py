# Imports once again...
import json
import webbrowser
from datetime import datetime

from .utils import cls, pprint, pinput


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
        categories = "{RESET}, {BLUE}".join(category_options)

        # Display transaction info to user and have user classify the transaction. If user input is not valid, ask again
        while True:
            if transaction_type == "income":
                category = pinput(
                    f"\nWhat category does the following {{GREEN}}{transaction_type}{{RESET}} transaction come "
                    f"under?\n\n"
                    f"Month: {{BLUE}}{month}{{RESET}}\n"
                    f"Amount: {{GREEN}}{currency_symbol}{amount}{{RESET}}\n"
                    f"Vendor: {{BLUE}}{vendor.title()}{{RESET}}\n"
                    f"Reference: {{BLUE}}{reference}{{RESET}}\n"
                    f"Category options are: {{BLUE}}{categories}{{RESET}}\n"
                    f"Alternatively type {{BLUE}}ignore{{RESET}} to ignore this transaction.\n\n").lower().strip()
            else:
                category = pinput(
                    f"\nWhat category does the following {{RED}}{transaction_type}{{RESET}} transaction come under?\n\n"
                    f"Month: {{BLUE}}{month}{{RESET}}\n"
                    f"Amount: {{RED}}{currency_symbol}{amount}{{RESET}}\n"
                    f"Vendor: {{BLUE}}{vendor.title()}{{RESET}}\n"
                    f"Reference: {{BLUE}}{reference}{{RESET}}\n"
                    f"Category options are: {{BLUE}}{categories}{{RESET}}\n"
                    f"Alternatively type {{BLUE}}ignore{{RESET}} to ignore this transaction.\n\n").lower().strip()

            if category == "ignore":
                cls()
                return ""
            elif category not in category_options:
                pprint("\n{RED}Invalid category.{RESET}")
                continue
            else:
                break

        # Ask if user wants to save the category as default for categories of this type with this vendor if vendor is
        # not blank
        if vendor != "":
            while True:
                user_input = pinput(
                    f"\nWould you like to save {{BLUE}}{category}{{RESET}} as the category for "
                    f"{{BLUE}}{transaction_type}{{RESET}} transactions with {{BLUE}}{vendor.title()}{{RESET}}? "
                    f"[{{GREEN}}Y{{RESET}}/{{RED}}N{{RESET}}]:\n").lower().strip()
                cls()

                try:
                    if user_input[0] not in ["y", "n"]:
                        raise IndexError
                    else:
                        break
                except IndexError:
                    pprint("\n{RED}Invalid input.{RESET}")
                    continue

            # If user wants category saved, dave it and update the category mapping file
            if user_input[0] == "y":
                category_map[vendor] = category
                update_category_map(transaction_type, category_map)
                pprint("\n{GREEN}Category saved.{RESET}")
            else:
                pprint("\n{RED}Category not saved.{RESET}")

        # Return transaction category
        return category


# If user doesn't bank with bank already saved, get CSV headings from user for new bank, then return it
def parse_bank(user_and_bank_data, transaction_data):
    # Gets name of user's bank and confirms it
    while True:
        user_bank = input("\nWhat is the name of your bank?\n").strip()

        while True:
            user_input = pinput(f"\nYour bank is {{BLUE}}{user_bank}{{RESET}}, is that "
                                f"correct? [{{GREEN}}Y{{RESET}}/{{RED}}N{{RESET}}]:\n").lower().strip()
            cls()

            try:
                if user_input[0] not in ["y", "n"]:
                    raise IndexError
                else:
                    break
            except IndexError:
                pprint("\n{RED}Invalid input.{RESET}")
                continue

        if user_input[0] == "y":
            break

    # Formats and saves user's bank name
    user_bank_lowered = user_bank.lower().replace(" ", "-")
    user_and_bank_data["user"]["bank"] = user_bank_lowered
    user_and_bank_data["banks"][user_bank_lowered] = {}

    # Provides user with information on the process that is about to occur
    pinput("\nYou will now be asked to identify the header titles corresponding to certain pieces of information in "
           "your CSV of transaction data from your bank. Your answers are case sensitive, so please take care when "
           "typing. Press {BLUE}Enter{RESET} to continue.\n")

    required_info = ["date", "vendor", "amount", "reference"]

    # Gets user to input CSV headers for all required information
    for info in required_info:
        while True:
            csv_header = pinput(f"\nWhat is the header for the {{BLUE}}{info}{{RESET}} information in your CSV "
                                f"file?\n").strip()
            cls()

            try:
                transaction_data[csv_header]
            except KeyError:
                pprint("\n{RED}That doesn't seem to be a valid header, please try again.{RESET}\n")
                continue
            break

        user_and_bank_data["banks"][user_bank_lowered][info] = csv_header

        # If date information, date format is also needed, so asks user to determine and input
        if info == "date":
            pinput("\nAs well as the CSV header for the date information, the program also needs to know the format in "
                   "which the date is displayed in the CSV. Please input this using a datetime format, such as "
                   "{BLUE}%d/%m/%Y{RESET}. Once you press {BLUE}Enter{RESET}, a browser window will open and "
                   "display possible formatting codes.\n")
            cls()

            webbrowser.open("https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes")

            example_date = transaction_data[user_and_bank_data["banks"][user_bank_lowered]["date"]][0]

            while True:
                date_format = input("\nPlease input the date format for your CSV file:\n").strip()
                cls()

                try:
                    datetime.strptime(example_date, date_format)
                except:
                    pprint("\n{RED}That doesn't seem to be the right date format.{RESET} Try again.\n")
                    continue
                break

            user_and_bank_data["banks"][user_bank_lowered]["date_format"] = date_format

    # Determines if CSV contains transaction IDs, and if so, asks user to input CSV header
    while True:
        user_input = pinput("\nDoes your CSV file contain transaction IDs? "
                            "[{GREEN}Y{RESET}/{RED}N{RESET}]:\n").lower().strip()
        cls()

        try:
            if user_input[0] not in ["y", "n"]:
                raise IndexError
            else:
                break
        except IndexError:
            pprint("\n{RED}Invalid input.{RESET}")
            continue

    if user_input[0] == "y":
        while True:
            csv_header = input(f"\nWhat is the header for the transaction ID information in your CSV "
                               f"file?\n").strip()
            cls()

            try:
                transaction_data[csv_header]
            except KeyError:
                pprint("\n{RED}That doesn't seem to be a valid header, please try again.{RESET}\n")
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

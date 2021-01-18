# Imports once again...
import json
import webbrowser
from datetime import datetime

from .utils import cls


# Function to parse the transaction category for an incoming transaction
def parse_category(transaction_type, month, vendor, amount, reference, category_options, currency_symbol):
    # Retrieve the category map
    category_map = get_category_map(transaction_type)

    # If we already have the category stored return it
    if vendor in category_map:
        return category_map[vendor]
    else:
        # Create a string of categories to display to the user
        categories = ", ".join(category_options)

        # Display transaction info to user and have user classify the transaction. If user input is not valid, ask again
        while True:
            category = input(
                f"\nWhat category does the following {transaction_type} transaction come under?\n\n"
                f"Month: {month}\n"
                f"Amount: {currency_symbol}{amount}\n"
                f"Vendor: {vendor.title()}\n"
                f"Reference: \"{reference}\"\n"
                f"Category options are: {categories}\n\n").lower().strip()

            if category not in category_options:
                print("\nInvalid category.")
                continue
            else:
                break

        # Ask if user wants to save the category as default for categories of this type with this vendor if vendor is
        # not blank
        if vendor != "":
            while True:
                user_input = input(
                    f"\nWould you like to save {category} as the category for {transaction_type} transactions "
                    f"with {vendor.title()}? [Y/N]:\n").lower().strip()
                cls()

                try:
                    if user_input[0] not in ["y", "n"]:
                        raise IndexError
                    else:
                        break
                except IndexError:
                    print("\nInvalid input.")
                    continue

            # If user wants category saved, dave it and update the category mapping file
            if user_input[0] == "y":
                category_map[vendor] = category
                update_category_map(transaction_type, category_map)
                print("\nCategory saved.")
            else:
                print("\nCategory not saved.")

        # Return transaction category
        return category


# If user doesn't bank with bank already saved, get CSV headings from user for new bank, then return it
def parse_bank(user_and_bank_data, transaction_data):
    while True:
        user_bank = input("\nWhat is the name of your bank?\n").strip()

        while True:
            user_input = input(f"\nYour bank is {user_bank}, is that correct? [Y/N]:\n").lower().strip()
            cls()

            try:
                if user_input[0] not in ["y", "n"]:
                    raise IndexError
                else:
                    break
            except IndexError:
                print("\nInvalid input.")
                continue

        if user_input[0] == "y":
            break

    user_bank_lowered = user_bank.lower().replace(" ", "-")

    user_and_bank_data["user"]["bank"] = user_bank_lowered
    user_and_bank_data["banks"][user_bank_lowered] = {}

    print("\nYou will now be asked to identify the header titles corresponding to certain pieces of information in your"
          " CSV of transaction data from your bank. Your answers are case sensitive, so please take care when typing."
          "\n")

    required_info = ["date", "vendor", "amount", "reference"]

    for info in required_info:
        while True:
            csv_header = input(f"\nWhat is the header for the {info} information in your CSV file?\n").strip()
            cls()

            try:
                transaction_data[csv_header]
            except KeyError:
                print("\nThat doesn't seem to be a valid header, please try again.\n")
                continue
            break

        user_and_bank_data["banks"][user_bank_lowered][info] = csv_header

        if info == "date":
            input("\nAs well as the CSV header for the date information, the program also needs to know the format in "
                  "which the date is displayed in the CSV. Please input this using a datetime format, such as "
                  "\"%d/%m/%Y\". Once you press Enter, a browser window will open and display possible formatting "
                  "codes.\n")
            cls()

            webbrowser.open("https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes")

            example_date = transaction_data[user_and_bank_data["banks"][user_bank_lowered]["date"]][0]

            while True:
                date_format = input("\nPlease input the date format for your CSV file:\n").strip()
                cls()

                try:
                    datetime.strptime(example_date, date_format)
                except:
                    print("\nThat doesn't seem to be the right date format. Try again.\n")
                    continue
                break

            user_and_bank_data["banks"][user_bank_lowered]["date_format"] = date_format

    while True:
        user_input = input("\nDoes your CSV file contain transaction IDs? [Y/N]:\n").lower().strip()
        cls()

        try:
            if user_input[0] not in ["y", "n"]:
                raise IndexError
            else:
                break
        except IndexError:
            print("\nInvalid input.")
            continue

    if user_input[0] == "y":
        while True:
            csv_header = input(f"\nWhat is the header for the transaction ID information in your CSV "
                               f"file?\n").strip()
            cls()

            try:
                transaction_data[csv_header]
            except KeyError:
                print("\nThat doesn't seem to be a valid header, please try again.\n")
                continue
            break

        user_and_bank_data["banks"][user_bank_lowered]["transaction_id"] = csv_header
    else:
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

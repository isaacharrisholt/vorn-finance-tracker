# Imports...
import json
import sys

from lib import logic
from lib import spreadsheet_manager as sm
from lib.utils import cls, pprint, pinput

cls()

transaction_data = logic.get_transaction_data(sys.argv)
xlsx_path = logic.get_spreadsheet_path(sys.argv)

# Gets user and bank data from file
with open("files/user_and_bank_data.json", "r") as user_and_bank_data_file:
    user_and_bank_data = json.load(user_and_bank_data_file)
    user_and_bank_data_file.close()

if user_and_bank_data["user"]["bank"] == "":
    user_bank = logic.get_bank(user_and_bank_data, transaction_data)
else:
    user_bank = user_and_bank_data["user"]["bank"]

# Checks if user already has a currency symbol set as default. If not, user chooses one.
if user_and_bank_data["user"]["currency"] == "":
    currency_symbol = logic.get_currency(user_and_bank_data)
else:
    currency_symbol = user_and_bank_data["user"]["currency"]

cls()

while True:
    user_selection = pinput(f"What would you like to do?\n"
                            f"Please select an option from the list below.\n\n"
                            f"Your currently selected bank is: {{YELLOW}}{user_bank.title()}{{RESET}}\n"
                            f"Your current currency symbol is: {{YELLOW}}{currency_symbol}{{RESET}}\n\n"
                            f"1. Run the program\n"
                            f"2. Switch bank / Set up a new bank\n"
                            f"3. Change currency symbol\n"
                            f"4. Quit").strip()

    cls()

    try:
        user_selection = int(user_selection)
        if user_selection == 1:
            break
        elif user_selection == 2:
            user_bank = logic.get_bank(user_and_bank_data, transaction_data)
        elif user_selection == 3:
            currency_symbol = logic.get_currency(user_and_bank_data)
        elif user_selection == 4:
            exit()
        else:
            raise ValueError
    except ValueError:
        pprint("{RED}Invalid selection, try again.{RESET}")

transaction_df, use_transaction_id = logic.create_transaction_df(user_and_bank_data, transaction_data)

# Deletes old DataFrame as it's no longer needed, and may be quite large
del transaction_data

categories = logic.get_categories()

# Loads transaction history (a list of previously processed transaction IDs)
with open("files/transaction_history.json", "r") as transaction_history_file:
    transaction_history = json.load(transaction_history_file)
    transaction_history_file.close()

# Creates a copy of transaction history that won't be edited for totalling later in the program
transaction_history_for_totals = transaction_history.copy()

transaction_df, transaction_history = logic.update_transaction_df(transaction_df, transaction_history,
                                                                  use_transaction_id, categories, currency_symbol)

# Two variables to store total amount spent and received across all transactions
can_use = ~transaction_df["Transaction IDs"].isin(transaction_history_for_totals)
total_in = round(transaction_df[transaction_df["Categories"] != ""].where(can_use).loc[transaction_df["Amounts"] > 0,
                                                                                       "Amounts"].sum(), 2)
total_out = round(abs(transaction_df[transaction_df["Categories"] != ""].where(can_use).loc[transaction_df["Amounts"] <
                                                                                            0, "Amounts"].sum()), 2)

# Inserts data into spreadsheet
sm.insert_into_spreadsheet(xlsx_path, categories, transaction_df)

if use_transaction_id:
    # Saves transaction history
    with open("files/transaction_history.json", "w") as transaction_history_file:
        json.dump(transaction_history, transaction_history_file, indent=4)
        transaction_history_file.close()

# Final statement to user
pprint(f"Done!\nTotal money in: {{GREEN}}{currency_symbol}{total_in}{{RESET}}\n"
       f"Total money out: {{RED}}{currency_symbol}{total_out}\n"
       f"{{RESET}}Net change: {{YELLOW}}{currency_symbol}{round(total_in - total_out, 2)}{{RESET}}")

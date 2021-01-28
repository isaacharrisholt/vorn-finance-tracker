import openpyxl as opxl

from .utils import cls, pprint, pinput


# Function to update the spreadsheet with cumulative transaction data
def insert_into_spreadsheet(filename, categories, transaction_df):
    # Opens spreadsheet as an openpyxl Workbook
    workbook = opxl.load_workbook(filename=filename)
    sheet = workbook.active

    # Iterates through transactions
    for month in range(1, 13):
        # Uses unicode values to calculate the spreadsheet column letter for this month
        column = chr(65 + month)

        # Iterates through outgoings and adds to spreadsheet
        for category in categories["outgoings"]:

            # Gets amount from transaction DataFrame
            amount = round(abs(transaction_df.loc[(transaction_df["Months"] == month) &
                                                  (transaction_df["Categories"] == category) &
                                                  (transaction_df["Amounts"] < 0),
                                                  "Amounts"].sum()), 2)
            # Gets row from categories dictionary
            row = categories["outgoings"][category]

            if amount != 0:
                val = sheet[column + row].value
                # If/else statement assures nothing is overwritten and values are cumulative
                if isinstance(val, int) or isinstance(val, float):
                    sheet[column + row] = val + amount
                else:
                    sheet[column + row] = amount

        # Same as above for income
        for category in categories["income"]:

            amount = round(abs(transaction_df.loc[(transaction_df["Months"] == month) &
                                                  (transaction_df["Categories"] == category) &
                                                  (transaction_df["Amounts"] > 0),
                                                  "Amounts"].sum()), 2)
            row = categories["income"][category]

            if amount != 0:
                val = sheet[column + row].value
                if isinstance(val, int) or isinstance(val, float):
                    sheet[column + row] = val + amount
                else:
                    sheet[column + row] = amount

    # Attempts to save the spreadsheet and alerts user if this isn't possible due to the spreadsheet being open in
    # another program
    while True:
        try:
            workbook.save(filename=filename)
            pprint("{GREEN}Spreadsheet saved.{RESET}")
        except PermissionError:
            pinput("{RED}Spreadsheet permission denied.{GREEN} This usually happens because the spreadsheet is open in "
                   "another program. If the spreadsheet is open, try closing it, then press {YELLOW}Enter{RESET} to "
                   "continue.")
            cls()
            continue
        break


# Function to validate that a given path leads to a spreadsheet file
def validate_spreadsheet(filename):
    # Tries to open spreadsheet using openpyxl, and returns True if it can, else returns False
    try:
        opxl.load_workbook(filename=filename)
    except (opxl.utils.exceptions.InvalidFileException, FileNotFoundError):
        return False
    return True

import openpyxl as opxl

# Map rows in spreadsheet to transaction category for both outgoings and income
outgoings_rows = {"7": "food", "8": "transport", "10": "rent", "12": "savings-deposit",
                  "15": "entertainment", "16": "eating-out", "17": "random-expenses", "18": "other"}

income_rows = {"23": "job", "24": "other-work", "27": "savings-withdrawal", "28": "refunds", "31": "birthday",
               "32": "christmas", "33": "other-gifts"}


# Function to update the spreadsheet with cumulative transaction data
def insert_into_spreadsheet(filename, outgoings, income):
    # Opens spreadsheet as an openpyxl Workbook
    workbook = opxl.load_workbook(filename=filename)
    sheet = workbook.active

    # Iterates through transactions
    # Note: as both outgoings and income dictionaries have the same structure, it doesn't matter which we iterate
    # through here
    for month in outgoings:
        # Uses unicode values to calculate the spreadsheet column letter for this month
        column = chr(65 + month)

        # Iterates through outgoings and adds to spreadsheet
        for key in outgoings_rows.keys():
            if outgoings[month][outgoings_rows[key]] != 0:
                val = sheet[column + key].value
                # If/else statement assures nothing is overwritten and values are cumulative
                if isinstance(val, int) or isinstance(val, float):
                    sheet[column + key] = val + outgoings[month][outgoings_rows[key]]
                else:
                    sheet[column + key] = outgoings[month][outgoings_rows[key]]

        # Same as above for income
        for key in income_rows.keys():
            if income[month][income_rows[key]] != 0:
                val = sheet[column + key].value
                if isinstance(val, int) or isinstance(val, float):
                    sheet[column + key] = val + income[month][income_rows[key]]
                else:
                    sheet[column + key] = income[month][income_rows[key]]

    # Attempts to save the spreadsheet and alerts user if this isn't possible due to the spreadsheet being open in
    # another program
    while True:
        try:
            workbook.save(filename=filename)
            print("\nSpreadsheet saved.")
        except PermissionError:
            input("\nSpreadsheet permission denied. This usually happens because the spreadsheet is open in another "
                  "program. If the spreadsheet is open, try closing it, then press Enter to continue.")
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

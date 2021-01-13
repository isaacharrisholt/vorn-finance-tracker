import openpyxl as opxl


# Function to update the spreadsheet with cumulative transaction data
def insert_into_spreadsheet(filename, outgoings_categories, income_categories, outgoings_balances, income_balances):
    # Opens spreadsheet as an openpyxl Workbook
    workbook = opxl.load_workbook(filename=filename)
    sheet = workbook.active

    # Iterates through transactions
    # Note: as both outgoings and income dictionaries have the same structure, it doesn't matter which we iterate
    # through here
    for month in outgoings_balances:
        # Uses unicode values to calculate the spreadsheet column letter for this month
        column = chr(65 + month)

        # Iterates through outgoings and adds to spreadsheet
        for category in outgoings_categories:

            amount = outgoings_balances[month][category]
            row = outgoings_categories[category]

            if amount != 0:
                val = sheet[column + row].value
                # If/else statement assures nothing is overwritten and values are cumulative
                if isinstance(val, int) or isinstance(val, float):
                    sheet[column + row] = val + amount
                else:
                    sheet[column + row] = amount

        # Same as above for income
        for category in income_categories:

            amount = income_balances[month][category]
            row = income_categories[category]

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

# Only one import yayyyyy...
import json


# Function to parse the transaction category for an incoming transaction
def parse_category(transaction_type, month, vendor, amount, reference, category_options):
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
                f"\n\n\nWhat category does the following {transaction_type} transaction come under?\n\n"
                f"Month: {month}\n"
                f"Amount: £{amount}\n"
                f"Vendor: {vendor.title()}\n"
                f"Reference: \"{reference}\"\n"
                f"Category options are: {categories}\n\n").lower()
            if category not in category_options:
                print("Invalid category.")
                continue
            else:
                break

        # Ask if user wants to save the category as default for categories of this type with this vendor
        while True:
            user_input = input(
                f"\nWould you like to save {category} as the category for {transaction_type} transactions "
                f"with {vendor.title()}? [Y/N]:\n").lower()

            try:
                if user_input[0] not in ["y", "n"]:
                    raise IndexError
                else:
                    break
            except IndexError:
                print("Invalid input")
                continue

        # If user wants category saved, dave it and update the category mapping file
        if user_input[0] == "y":
            category_map[vendor] = category
            update_category_map(transaction_type, category_map)
            print("Category saved.")
        else:
            print("Category not saved.")

        # Return transaction category
        return category


# Function to get the category map as a dictionary for a given transaction type
def get_category_map(transaction_type):
    with open(f"files/mappings/{transaction_type}_mapping.json", "r") as f:
        category_map = json.load(f)
        f.close()
    return category_map


# Function to update the category map file of a given transaction type
def update_category_map(transaction_type, category_map):
    with open(f"files/mappings/{transaction_type}_mapping.json", "w") as f:
        json.dump(category_map, f)
        f.close()

# Vorn Finance Tracker

Vorn Finance Tracker is a Python program that categorises your income and spending and writes the data into a
spreadsheet. It works with any bank account that allows you to export a CSV file containing your transactions (support
for QIF files coming soon). 

Note: if you bank with Santander and download your CSV file through their "Midata" system, check it before you run the
program, as it's usually horrifically formatted, even for a CSV file. This isn't something I can correct, and is down
to Santander themselves to sort. Sorry folks.

## Prerequisite Software

### Windows

None! Everything is provided in the `venv` folder. However, if you don't want to run it that way, you can install the
prerequisites using `install_prerequesites.bat` after installing Python 3.

### Mac and Linux

Again, nothing needed, but if you prefer not to use the `venv-unix` virtual environment, run `install_prerequisites.sh`
from the terminal and the following things will be installed.

- [Python 3](https://www.python.org/) (make sure to add Python to PATH/environment variables when installing)
- [pandas 1.2.0 or newer](https://pandas.pydata.org/)
- [openpyxl 3.0.5 or newer](https://pypi.org/project/openpyxl/)
- [colorama 0.4.4 or newer](https://pypi.org/project/colorama/) (optional, enables colours in command line output)

## Installation

Vorn Finance Tracker can either be installed by downloading the repository from
[the GitHub page](https://github.com/isaacharrisholt/vorn-finance-tracker) or by running the following command if git
is installed on your machine:
```commandline
git clone https://github.com/isaacharrisholt/vorn-finance-tracker
```

## Usage
In order to use Vorn Finance Tracker, you need two things:
1. A CSV file downloaded from your bank containing your transaction data.
   - This will be different depending on your bank, so you may have to Google how to get hold of one. 
2. A spreadsheet for the data to be output into.
   - A `spreadsheet_template.xlsx` is included in the program files. Feel free to copy and modify that in any way you
    like. See [Using Custom Categories](#using-custom-categories) for info on how to use categories other than the 
     default, so you can customise the spreadsheet to your liking.
     
Now follow the instructions for your operating system below.

### Windows

Run the `start.bat` file. That's it. Bish bash bosh.

Alternatively, follow the instructions for Mac and Linux, making sure to use Windows file paths in the command. Only do
this if you ran `install_prerequisites.bat` earlier.

### Mac and Linux

Run the `start_unix.sh` file. You can do this with the following command:

```commandline
source start_unix.sh
```

### Using the program

If it's your first time running the program, it will ask you who you bank with and what currency symbol to use. This is
so that the program can parse the data from your CSV file correctly. There are a few banks pre-programmed, but if yours
isn't included, type `other` and follow the steps in the command terminal.

The following banks are currently pre-programmed:
```text
Monzo
Starling
```
The reason there aren't more is because I don't have accounts with other banks that allow me to easily access a CSV file
of transactions. If you want your bank supported by default, see [Contribute](#contribute).

If you have switched bank or currency, press `2` or `3` respectively when the menu appears.

The program will then guide you through the rest of the process yourself, but should you have any issues, please raise
them with [@isaacharrisholt](https://github.com/isaacharrisholt).

### Using Custom Categories

If you'd prefer not to use the default categories and want to change the location of things in the spreadsheet, or even
have your own spreadsheet layout you'd prefer to use, that's entirely possible (see
[Customising Spreadsheet Layout](#customising-spreadsheet-layout) for more details).

In order to customise your income or spending categories, simply modify either `files/income_categories.txt` or
`files/outgoings_categories.txt` respectively.

For example, the default `outgoings_categories.txt` looks like this:

```text
food: 7
transport: 8
rent: 9
savings deposit: 12
entertainment: 15
eating out: 16
random expenses: 17
other: 18
```

Each line is in the format `category: row_number` where `row_number` correlates to the row number you'd like the data 
for that category to be inserted into in the spreadsheet.

If you wanted to keep track of say, laundry costs in your spreadsheet (if you use a laundrette for example) and wanted 
to store the data in row 19, you would simply add `laundry: 19` to a new line:

```text
food: 7
transport: 8
rent: 9
savings deposit: 12
entertainment: 15
eating out: 16
random expenses: 17
other: 18
laundry: 19
```

Spaces are acceptable, and case does not matter (the program converts everything to lowercase anyway). The order of the 
categories doesn't matter, but you may prefer to keep them in the order you've got them in your spreadsheet. The program
will also filter out any duplicate categories, though the row will be overwritten, so if you do something like this...

```text
laundry: 19
laundry: 20
```

...your laundry spending will be put in row 20.

Aaaaaaand you're done! Your new category has been added and will be taken into account next time you run the program.

### Customising Spreadsheet Layout

By default, the program will use rows B-M of the spreadsheet for months Jan-Dec respectively. You can shift this left
and right by modifying `lib/spreadsheet_manager.py`. The following piece of code is on line 15:
```python
column = chr(65 + month)
```

By changing the number `65`, you can place January in different columns, and Feb, Mar etc. will follow on to the right
from there.

64 represents column A, 65 is B and so on. I have plans to allow for more customisation, such as rotating the data so
that the months run down the rows, and transaction categories are the column headers, but that's a little ways off yet.

## To-Dos

There are a few more things I want to do with this project. The current to-do list is below, but if you think of
anything you'd like added, please let me know!

- [x] Make category customisation more user-friendly
- [x] Expand support to all banks
- [x] Better utilise the pandas library to optimise program speed
- [x] Improve user experience
- [ ] Expand spreadsheet customisation options
- [ ] Add a GUI
- [ ] \(Maybe) Integrate with banking APIs so transactions can be obtained programmatically

## Contribute

Pull requests welcome, though if you want to make a major change, please open an issue first for discussion.

If you'd like to provide me with a CSV file from your bank so I can pre-program it into the software, please open an
issue or message [@isaacharrisholt](https://github.com/isaacharrisholt).

## Credits

**Devs:**
- So far, just me.

**Inspiration:**
- [The Freakizoid](https://twitter.com/the_freakizoid) for telling me to get my financial ass into gear!

## License

Vorn Financial Tracker is licensed under [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html).
